import { useUniwind } from 'uniwind';
import { dark, light } from './kalamkari';

/** Kalamkari tokens for the current theme (follows Settings → Theme, which drives Uniwind). */
export function useKalamkari() {
  const { theme } = useUniwind();
  return theme === 'dark' ? dark : light;
}
