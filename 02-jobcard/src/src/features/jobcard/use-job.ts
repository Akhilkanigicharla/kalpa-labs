// State for one job on the Record screen: dictation → card → save (SQLite + outbox) → bill → share.
import type { Card } from '@core/parse.mjs';
import type { LocalDb } from '@/lib/jobcard/db';
import type { Technician } from '@/lib/jobcard/jobs';
import type { AppLang } from '@/lib/jobcard/voice';
import { parseTranscript } from '@core/parse.mjs';
import * as Crypto from 'expo-crypto';
import * as Haptics from 'expo-haptics';
import { useSpeechRecognitionEvent } from 'expo-speech-recognition';
import * as React from 'react';
import { openLocalDb } from '@/lib/jobcard/db';
import { makeBill, saveJob } from '@/lib/jobcard/jobs';
import { flush, pendingCount } from '@/lib/jobcard/outbox';
import { shareBill } from '@/lib/jobcard/share';
import { MAX_NOTE_MS, startDictation, stopDictation } from '@/lib/jobcard/voice';

let dbPromise: Promise<LocalDb> | null = null;
export const getDb = () => (dbPromise ??= openLocalDb());
export function resetDbForTests(db: LocalDb) { dbPromise = Promise.resolve(db); }

export const partsSum = (card: Card) => card.parts.reduce((s, p) => s + (p.rate ?? 0) * (p.qty || 1), 0);

type Opts = { lang: AppLang; online: boolean; techId: string | null; tech: Technician | null; sync?: Parameters<typeof flush>[1] };

export function useJob({ lang, online, techId, tech, sync }: Opts) {
  const [listening, setListening] = React.useState(false);
  const [text, setText] = React.useState('');
  const [audioUri, setAudioUri] = React.useState<string | null>(null);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [billNo, setBillNo] = React.useState<string | null>(null);
  const [pending, setPending] = React.useState(0);
  const [error, setError] = React.useState<string | null>(null);
  const finalRef = React.useRef('');
  const card = React.useMemo(() => (text.trim() ? parseTranscript(text) : null), [text]);

  useSpeechRecognitionEvent('result', (e) => {
    const t = e.results[0]?.transcript ?? '';
    if (e.isFinal) { finalRef.current = `${finalRef.current} ${t}`.trim(); setText(finalRef.current); }
    else {
      setText(`${finalRef.current} ${t}`.trim());
    }
  });
  useSpeechRecognitionEvent('audioend', (e) => {
    if (e.uri)
      setAudioUri(e.uri);
  });
  useSpeechRecognitionEvent('end', () => setListening(false));
  useSpeechRecognitionEvent('error', (e) => {
    setListening(false); if (e.error !== 'no-speech')
      setError(e.message);
  });

  React.useEffect(() => { // the 2-minute cap
    if (!listening)
      return;
    const t = setTimeout(() => { void stopDictation(); }, MAX_NOTE_MS);
    return () => clearTimeout(t);
  }, [listening]);

  const refreshPending = React.useCallback(async () => {
    const db = await getDb();
    if (sync && online)
      await flush(db, sync, { online });
    setPending(await pendingCount(db));
  }, [sync, online]);
  React.useEffect(() => { void refreshPending(); }, [refreshPending]);

  const toggleMic = React.useCallback(async () => {
    setError(null);
    if (listening) { await stopDictation(); setListening(false); return; }
    void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); // same frame as the visual press
    finalRef.current = text; setJobId(null); setBillNo(null);
    const ok = await startDictation(lang, online);
    if (!ok) { setError('mic_denied'); return; }
    setListening(true);
  }, [listening, lang, online, text]);

  const save = React.useCallback(async () => {
    if (!card || !techId)
      return;
    const db = await getDb();
    const r = await saveJob(db, card, { techId, newId: Crypto.randomUUID, audioUri });
    setJobId(r.jobId);
    void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    await refreshPending();
  }, [card, techId, audioUri, refreshPending]);

  const bill = React.useCallback(async () => {
    if (!jobId || !tech)
      return;
    try {
      const db = await getDb();
      const { meta, totals } = await makeBill(db, jobId, tech, { newId: Crypto.randomUUID });
      setBillNo(meta.number);
      await refreshPending();
      await shareBill(meta, totals);
    }
    catch (e) { setError((e as Error).message); }
  }, [jobId, tech, refreshPending]);

  const reset = React.useCallback(() => { finalRef.current = ''; setText(''); setAudioUri(null); setJobId(null); setBillNo(null); setError(null); }, []);

  return { listening, text, setText, card, jobId, billNo, pending, error, toggleMic, save, bill, reset };
}
