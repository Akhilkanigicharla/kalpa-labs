// Live dictation with the phone's own recogniser (free). Offline it uses the on-device model, and the
// audio is always kept (persist) so the server can transcribe it again with Sarvam when there is signal.
import type { ExpoSpeechRecognitionOptions } from 'expo-speech-recognition';
import { ExpoSpeechRecognitionModule as M } from 'expo-speech-recognition';

export type AppLang = 'te' | 'hi' | 'en';
export const LOCALE: Record<AppLang, string> = { te: 'te-IN', hi: 'hi-IN', en: 'en-IN' };
export const MAX_NOTE_MS = 120_000; // 2-minute cap keeps speech-to-text cost down (PLAN §3)

export function dictationOptions(lang: AppLang, online: boolean): ExpoSpeechRecognitionOptions {
  return {
    lang: LOCALE[lang] || 'te-IN',
    interimResults: true,
    continuous: true,
    addsPunctuation: false, // numbers matter more than commas; the parser reads "2500" not "2,500."
    requiresOnDeviceRecognition: !online,
    contextualStrings: ['gas refill', 'capacitor', 'service charge', 'jet service', 'PCB', 'compressor', 'split AC', 'window AC'],
    recordingOptions: { persist: true },
    androidIntentOptions: { EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS: 4000 },
  };
}

export async function startDictation(lang: AppLang, online: boolean): Promise<boolean> {
  const perm = await M.requestPermissionsAsync();
  if (!perm.granted)
    return false;
  M.start(dictationOptions(lang, online));
  return true;
}

export async function stopDictation() {
  M.stop();
}
