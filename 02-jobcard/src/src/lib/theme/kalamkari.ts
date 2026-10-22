// Kalpa design system "Kalpavruksha" for React Native. Values are copied from 00-hq/design/tokens.css;
// src/lib/theme/kalamkari.test.ts fails if they drift. JobCard's world colour is l2 (indigo-blue).
export const light = {
  'bg': '#F2EEE3',
  'panel': '#FCFAF4',
  'fg': '#1E2A1F',
  'muted': '#5A6152',
  'rule': '#DCD5C3',
  'soft': '#E9E3D3',
  'accent': '#2F6A3A',
  'accent-fg': '#FFFFFF',
  'madder': '#8A4A28',
  'leaf': '#5E9E4C',
  'bark': '#6B4226',
  'gold': '#C38E12',
  'flame': '#B35E26',
  'ok': '#2C7A43',
  'warn': '#A06400',
  'bad': '#B13A2D',
  'hero': '#1D3A25',
  'hero-fg': '#F4EEDC',
  'hero-mute': '#BFCDAE',
  'l0': '#66655A',
  'l1': '#8A4A28',
  'l2': '#2F6F78',
  'l3': '#3B7A3A',
  'l4': '#7A3F5E',
  'l5': '#9C700E',
  'l6': '#A8324F',
  'l7': '#4A5590',
} as const;

export const dark = {
  'bg': '#0F1912',
  'panel': '#16231A',
  'fg': '#ECE7D8',
  'muted': '#A8B39B',
  'rule': '#2A3A2D',
  'soft': '#1D2C21',
  'accent': '#8FCB8C',
  'accent-fg': '#0F1912',
  'madder': '#D98B5F',
  'leaf': '#8FCB8C',
  'bark': '#C08A5E',
  'gold': '#E8B64A',
  'flame': '#E5925A',
  'ok': '#6FD08F',
  'warn': '#E8B64A',
  'bad': '#F07A6B',
  'hero': '#17301F',
  'hero-fg': '#F4EEDC',
  'hero-mute': '#BFCDAE',
  'l0': '#B4B3A4',
  'l1': '#D98B5F',
  'l2': '#6FC2CB',
  'l3': '#6FD08F',
  'l4': '#D59AB9',
  'l5': '#E8B64A',
  'l6': '#FF7F9E',
  'l7': '#9DA8E6',
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
