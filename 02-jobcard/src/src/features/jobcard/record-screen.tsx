// Record · రికార్డ్ — speak the job, check the card, save, bill, share. One task per screen (design/BRIEF.md).
import type { Card } from '@core/parse.mjs';
import type { Technician } from '@/lib/jobcard/jobs';
import type { AppLang } from '@/lib/jobcard/voice';
import * as React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Animated, { useReducedMotion } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { translate, useSelectedLanguage } from '@/lib/i18n';
import { getItem } from '@/lib/storage';
import { bodyFonts, fonts, radius } from '@/lib/theme/kalamkari';
import { useKalamkari } from '@/lib/theme/use-kalamkari';
import { partsSum, useJob } from './use-job';

const EASE_OUT = 'cubic-bezier(0.23, 1, 0.32, 1)';
const rs = (n: number) => `₹${n.toLocaleString('en-IN')}`;
const MACHINE: Record<string, string> = { split_ac: 'Split AC', window_ac: 'Window AC', cassette_ac: 'Cassette AC', ac: 'AC', fridge: 'Fridge', washing_machine: 'Washing machine' };

function useStyles() {
  const { language } = useSelectedLanguage();
  const f = React.useMemo(() => bodyFonts(language), [language]);
  return { s: React.useMemo(() => makeStyles(f), [f]), f };
}

/** Press feedback: scale 0.97 on press-in, 120 ms strong ease-out, on the UI thread (Reanimated CSS transition). */
function PressScale({ children, onPress, style, testID, label, disabled }: { children: React.ReactNode; onPress: () => void; style: object; testID: string; label: string; disabled?: boolean }) {
  const [down, setDown] = React.useState(false);
  const reduced = useReducedMotion();
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      onPressIn={() => setDown(true)}
      onPressOut={() => setDown(false)}
      hitSlop={8}
      pressRetentionOffset={16}
    >
      <Animated.View style={[style, { opacity: disabled ? 0.45 : 1, transform: [{ scale: down && !reduced ? 0.97 : 1 }], transitionProperty: 'transform', transitionDuration: 120, transitionTimingFunction: EASE_OUT }]}>
        {children}
      </Animated.View>
    </Pressable>
  );
}

function Chip({ label, value, k }: { label: string; value?: string | null; k: ReturnType<typeof useKalamkari> }) {
  const { s, f } = useStyles();
  const gap = !value;
  return (
    <View style={[s.chip, { backgroundColor: gap ? k.soft : k.panel, borderColor: gap ? k.gold : k.rule }]}>
      <Text style={[s.small, { color: k.muted, fontFamily: f.body }]}>{label}</Text>
      <Text style={[s.body, { color: gap ? k.warn : k.fg, fontFamily: f.bold }]}>{value || translate('jobcard.unknown')}</Text>
    </View>
  );
}

function CardView({ card, k }: { card: Card; k: ReturnType<typeof useKalamkari> }) {
  const { s, f } = useStyles();
  const sum = partsSum(card);
  const unpriced = card.parts.filter(p => p.rate == null).map(p => p.desc);
  return (
    <View testID="job-card" style={[s.panel, { backgroundColor: k.panel, borderColor: k.rule }]}>
      <Text style={[s.label, { color: k.muted }]}>{translate('jobcard.heard')}</Text>
      <View style={s.chips}>
        <Chip k={k} label={translate('jobcard.customer')} value={card.customer.name} />
        <Chip k={k} label={translate('jobcard.phone')} value={card.customer.phone} />
        <Chip k={k} label={translate('jobcard.machine')} value={[card.appliance && MACHINE[card.appliance], card.brand].filter(Boolean).join(' · ')} />
      </View>
      {card.parts.map(p => (
        <View key={p.desc} style={[s.row, { borderBottomColor: k.rule }]}>
          <Text style={[s.body, { color: k.fg, fontFamily: f.body }]}>{p.desc}</Text>
          <Text style={[s.body, s.num, { color: p.rate == null ? k.warn : k.fg }]}>{p.rate == null ? '₹ ?' : rs(p.rate)}</Text>
        </View>
      ))}
      <View style={s.row}>
        <Text style={[s.body, { color: k.fg, fontFamily: f.bold }]}>{translate('jobcard.total')}</Text>
        <Text testID="total" style={[s.total, s.num, { color: k.fg }]}>{rs(sum)}</Text>
      </View>
      {card.total != null && card.total !== sum && (
        <Text testID="spoke-total" style={[s.small, { color: k.warn }]}>{translate('jobcard.spoke_total', { spoken: rs(card.total), sum: rs(sum) } as never)}</Text>
      )}
      {unpriced.length > 0 && <Text testID="price-needed" style={[s.small, { color: k.warn }]}>{translate('jobcard.price_needed', { parts: unpriced.join(', ') } as never)}</Text>}
    </View>
  );
}

export function RecordScreen({ online = true }: { online?: boolean }) {
  const k = useKalamkari();
  const { s, f } = useStyles();
  const insets = useSafeAreaInsets();
  const { language } = useSelectedLanguage();
  const tech = getItem<Technician>('technician');
  const job = useJob({ lang: (language || 'te') as AppLang, online, techId: tech?.id ?? null, tech });
  const canBill = !!job.jobId && !!job.card && job.card.parts.length > 0 && job.card.parts.every(p => p.rate != null) && !!tech;

  return (
    <ScrollView style={{ backgroundColor: k.bg }} contentContainerStyle={[s.page, { paddingTop: insets.top + 16, paddingBottom: insets.bottom + 24 }]} keyboardShouldPersistTaps="handled">
      <Text style={[s.h1, { color: k.accent }]}>JobCard</Text>
      <Text style={[s.body, { color: k.muted, fontFamily: f.body }]}>{translate('jobcard.title')}</Text>

      <View style={s.center}>
        <PressScale
          testID="mic"
          label={job.listening ? translate('jobcard.listening') : translate('jobcard.hold')}
          onPress={job.toggleMic}
          style={[s.mic, { backgroundColor: k.gold, borderColor: job.listening ? k.madder : k.panel, transitionProperty: 'borderColor', transitionDuration: 150 }]}
        >
          <Text style={[s.micIcon, { color: k.hero }]}>{job.listening ? '■' : '●'}</Text>
        </PressScale>
        <Text style={[s.body, { color: job.listening ? k.madder : k.fg, fontFamily: f.bold, marginTop: 12 }]}>
          {job.listening ? translate('jobcard.listening') : translate('jobcard.hold')}
        </Text>
        {!online && <Text testID="offline" style={[s.small, { color: k.muted }]}>{translate('jobcard.offline')}</Text>}
        {job.error && <Text testID="error" style={[s.small, { color: k.bad }]}>{job.error === 'mic_denied' ? translate('jobcard.mic_denied') : job.error}</Text>}
      </View>

      <TextInput
        testID="note"
        value={job.text}
        onChangeText={job.setText}
        multiline
        placeholder={translate('jobcard.type_instead')}
        placeholderTextColor={k.muted}
        style={[s.note, { color: k.fg, borderColor: k.rule, backgroundColor: k.panel, fontFamily: f.body }]}
      />

      {job.card && <CardView card={job.card} k={k} />}

      {job.card && !job.jobId && (
        <PressScale testID="save" label={translate('jobcard.save')} onPress={job.save} disabled={!tech} style={[s.btn, { backgroundColor: k.accent }]}>
          <Text style={[s.btnText, { color: k['accent-fg'] }]}>{translate('jobcard.save')}</Text>
        </PressScale>
      )}
      {job.jobId && (
        <>
          <Text testID="saved" style={[s.small, { color: k.ok }]}>{job.billNo ? translate('jobcard.billed', { number: job.billNo } as never) : translate('jobcard.saved')}</Text>
          <PressScale testID="bill" label={translate('jobcard.bill')} onPress={job.bill} disabled={!canBill || !!job.billNo} style={[s.btn, { backgroundColor: k.ok }]}>
            <Text style={[s.btnText, { color: k['accent-fg'] }]}>{translate('jobcard.bill')}</Text>
          </PressScale>
        </>
      )}
      <Text testID="sync" style={[s.small, { color: k.muted, textAlign: 'center' }]}>
        {job.pending ? translate('jobcard.pending', { count: job.pending } as never) : translate('jobcard.synced')}
      </Text>
    </ScrollView>
  );
}

const makeStyles = (f: ReturnType<typeof bodyFonts>) => StyleSheet.create({
  page: { paddingHorizontal: 16, gap: 12 },
  h1: { fontFamily: fonts.display, fontSize: 30 },
  center: { alignItems: 'center', paddingVertical: 12 },
  mic: { width: 132, height: 132, borderRadius: 66, alignItems: 'center', justifyContent: 'center', borderWidth: 6 },
  micIcon: { fontSize: 44 },
  note: { minHeight: 72, borderWidth: 1, borderRadius: radius.m, padding: 12, fontSize: 16 },
  panel: { borderWidth: 1, borderRadius: radius.l, padding: 14, gap: 6 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 6 },
  chip: { borderWidth: 1, borderRadius: radius.s, paddingHorizontal: 10, paddingVertical: 6, minWidth: 96 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: 'transparent' },
  label: { fontSize: 12, letterSpacing: 0.5, textTransform: 'uppercase', fontFamily: f.bold },
  body: { fontSize: 16 },
  small: { fontSize: 13, fontFamily: f.body },
  num: { fontVariant: ['tabular-nums'], fontFamily: f.bold },
  total: { fontSize: 22 },
  btn: { minHeight: 52, borderRadius: radius.m, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  btnText: { fontSize: 17, fontFamily: f.bold },
});
