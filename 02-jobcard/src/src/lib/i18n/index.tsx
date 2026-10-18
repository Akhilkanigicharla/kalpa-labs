/* eslint-disable react-refresh/only-export-components */
import { getLocales } from 'expo-localization';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { I18nManager } from 'react-native';

import { resources } from './resources';
import { getLanguage } from './utils';

export * from './utils';

// Telugu unless the phone is set to Hindi or English
export function pickLanguage(code?: string | null): 'te' | 'hi' | 'en' {
  return code === 'hi' || code === 'en' ? code : 'te';
}

i18n.use(initReactI18next).init({
  resources,
  lng: getLanguage() || pickLanguage(getLocales()[0]?.languageCode),
  fallbackLng: 'en',
  supportedLngs: ['te', 'hi', 'en'],
  compatibilityJSON: 'v4', // Updated to v4 for i18next compatibility

  // allows integrating dynamic values into translations.
  interpolation: {
    escapeValue: false, // escape passed in values to avoid XSS injections
  },
});

// Is it a RTL language?
export const isRTL: boolean = i18n.dir() === 'rtl';

I18nManager.allowRTL(isRTL);
I18nManager.forceRTL(isRTL);

export default i18n;
