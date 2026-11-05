// Every JobCard bot message exists in all 5 languages (Akhil, 5 Nov 2026): en, te, hi, Tenglish, Hinglish.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../bot/functions/jobcard.js", import.meta.url), "utf8");
const block = src.slice(src.indexOf("const S = {"), src.indexOf("\n};", src.indexOf("const S = {")) + 3);
const S = new Function(block.replace("const S =", "return"))();
test("5 languages, same keys, same {placeholders}", () => {
  assert.deepEqual(Object.keys(S).sort(), ["en", "hi", "hi-latn", "te", "te-latn"]);
  for (const lang of Object.keys(S)) {
    assert.deepEqual(Object.keys(S[lang]).sort(), Object.keys(S.en).sort(), lang);
    for (const k of Object.keys(S.en)) assert.deepEqual((S[lang][k].match(/\{\w+\}/g) || []).sort(), (S.en[k].match(/\{\w+\}/g) || []).sort(), `${lang}.${k}`);
  }
});
