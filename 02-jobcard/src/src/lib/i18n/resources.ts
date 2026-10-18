import en from '@/translations/en.json';
import hi from '@/translations/hi.json';
import te from '@/translations/te.json';

// JobCard speaks Telugu first (Hyderabad technicians), then Hindi and English. No RTL language.
export const resources = {
  te: { translation: te },
  hi: { translation: hi },
  en: { translation: en },
};

export type Language = keyof typeof resources;
