import { Redirect, Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as React from 'react';

import { Text } from '@/components/ui';
import { Settings as SettingsIcon } from '@/components/ui/icons';
import { useAuthStore as useAuth } from '@/features/auth/use-auth-store';
import { useIsFirstTime } from '@/lib/hooks/use-is-first-time';
import { translate, useSelectedLanguage } from '@/lib/i18n';
import { bodyFonts } from '@/lib/theme/kalamkari';
import { useKalamkari } from '@/lib/theme/use-kalamkari';

export default function TabLayout() {
  const status = useAuth.use.status();
  const k = useKalamkari();
  const { language } = useSelectedLanguage();
  const insets = useSafeAreaInsets();
  const [isFirstTime] = useIsFirstTime();

  if (isFirstTime) {
    return <Redirect href="/onboarding" />;
  }
  if (status === 'signOut') {
    return <Redirect href="/login" />;
  }
  return (
    <Tabs
      screenOptions={{
        animation: 'none', // tabs are peers: never slide
        tabBarActiveTintColor: k.l2,
        tabBarInactiveTintColor: k.muted,
        // Telugu needs a taller line than the default 49 px bar
        tabBarStyle: { backgroundColor: k.panel, borderTopColor: k.rule, height: 70 + insets.bottom, paddingTop: 6, paddingBottom: insets.bottom + 8 },
        tabBarLabelStyle: { fontFamily: bodyFonts(language).bold, fontSize: 13, lineHeight: 26 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: translate('jobcard.tab'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>●</Text>,
          tabBarButtonTestID: 'record-tab',
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: translate('settings.title'),
          headerShown: false,
          tabBarIcon: ({ color }) => <SettingsIcon color={color} />,
          tabBarButtonTestID: 'settings-tab',
        }}
      />
    </Tabs>
  );
}
