import fs from 'node:fs';
import path from 'node:path';
import en from '@/translations/en.json';
import hi from '@/translations/hi.json';
import te from '@/translations/te.json';
import { dark, light } from './kalamkari';

const css = fs.readFileSync(path.join(__dirname, '../../../../../00-hq/design/tokens.css'), 'utf8');
const block = (start: string) => css.split(start)[1].split('}')[0];
const colours = (b: string) => Object.fromEntries([...b.matchAll(/--([a-z0-9-]+):(#[0-9A-F]{6})/gi)].map(m => [m[1], m[2]]));

it('react Native tokens are exactly the Kalamkari tokens (light + dark)', () => {
  expect(light).toEqual(colours(block(':root{')));
  expect(dark).toEqual(colours(block(':root[data-theme="dark"]{')));
});

it('te and hi have every English string, and none is left in English by mistake', () => {
  const keys = (o: object, p = ''): string[] => Object.entries(o).flatMap(([k, v]) => (typeof v === 'object' ? keys(v, `${p}${k}.`) : [`${p}${k}`]));
  expect(keys(te).sort()).toEqual(keys(en).sort());
  expect(keys(hi).sort()).toEqual(keys(en).sort());
  expect(te.jobcard.hold).toMatch(/[ఀ-౿]/); // Telugu script
  expect(hi.jobcard.hold).toMatch(/[ऀ-ॿ]/); // Devanagari
});
