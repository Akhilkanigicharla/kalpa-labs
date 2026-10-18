// Kalpa design system "Kalamkari" for React Native. Values are copied from 00-hq/design/tokens.css;
// src/lib/theme/kalamkari.test.ts fails if they drift. JobCard's world colour is l2 (indigo-blue).
export const light = {
  'bg': '#EEEDF3',
  'panel': '#FBFBFD',
  'fg': '#191C33',
  'muted': '#5D6079',
  'rule': '#DCDBE7',
  'soft': '#E6E6F1',
  'accent': '#2A3A8F',
  'accent-fg': '#FFFFFF',
  'madder': '#B23A2C',
  'gold': '#D3940A',
  'flame': '#C2541B',
  'ok': '#23804F',
  'warn': '#B86E00',
  'bad': '#C0392B',
  'hero': '#1C2463',
  'hero-fg': '#F6F2E8',
  'hero-mute': '#B9BDE0',
  'l0': '#5B6178',
  'l1': '#B23A2C',
  'l2': '#2F4FB0',
  'l3': '#2E7D4F',
  'l4': '#7B3F8C',
  'l5': '#C08304',
  'l6': '#B8235A',
  'l7': '#13777F',
} as const;

export const dark = {
  'bg': '#0E1230',
  'panel': '#161B42',
  'fg': '#ECEBF7',
  'muted': '#A3A7CC',
  'rule': '#2A3060',
  'soft': '#1F2552',
  'accent': '#9AABFF',
  'accent-fg': '#0E1230',
  'madder': '#F0745F',
  'gold': '#F2B840',
  'flame': '#F08A4B',
  'ok': '#5BD08F',
  'warn': '#F2B840',
  'bad': '#FF7A6B',
  'hero': '#1B2266',
  'hero-fg': '#F6F2E8',
  'hero-mute': '#B9BDE0',
  'l0': '#A5A9C6',
  'l1': '#F0745F',
  'l2': '#7C98FF',
  'l3': '#5BD08F',
  'l4': '#C792E0',
  'l5': '#F2B840',
  'l6': '#FF6F9F',
  'l7': '#45C6CF',
} as const;

export type Tokens = { [K in keyof typeof light]: string };
export const fonts = {
  display: 'RozhaOne_400Regular', // Latin only: Telugu never goes in the display face
  body: 'AnekLatin_400Regular',
  bodyBold: 'AnekLatin_700Bold',
  telugu: 'AnekTelugu_400Regular',
  teluguBold: 'AnekTelugu_700Bold',
} as const;
/** Body faces for the UI language: Anek Telugu carries Latin too, so Telugu screens use it throughout. */
export const bodyFonts = (lang?: string) => (lang === 'te' ? { body: fonts.telugu, bold: fonts.teluguBold } : { body: fonts.body, bold: fonts.bodyBold });
export const radius = { s: 8, m: 12, l: 18 } as const;
export const WORLD = 'l2' as const;
