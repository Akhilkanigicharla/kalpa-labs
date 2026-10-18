import { Redirect, Tabs } from 'expo-router';
import * as React from 'react';

import { Text } from '@/components/ui';
import { Settings as SettingsIcon } from '@/components/ui/icons';
import { useAuthStore as useAuth } from '@/features/auth/use-auth-store';
import { useIsFirstTime } from '@/lib/hooks/use-is-first-time';
import { translate } from '@/lib/i18n';

export default function TabLayout() {
  const status = useAuth.use.status();
  const [isFirstTime] = useIsFirstTime();

  if (isFirstTime) {
    return <Redirect href="/onboarding" />;
  }
  if (status === 'signOut') {
    return <Redirect href="/login" />;
  }
  return (
    <Tabs screenOptions={{ animation: 'none' }}>
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
