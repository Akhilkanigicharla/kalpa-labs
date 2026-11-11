import { describe, expect, it } from "vitest";
import { fitTitle, fitDescription } from "./seo";
import { CALCS } from "./calcs";
import { KITS } from "./kits";

const inTitle = (s: string) => s.length >= 30 && s.length <= 60;
const inDesc = (s: string) => s.length >= 70 && s.length <= 160;

describe("fitTitle / fitDescription", () => {
  it("drops the suffix when too long and adds the region when too short", () => {
    expect(fitTitle("RD calculator (bank and post office recurring deposit) | Free", "en")).toBe("RD calculator (bank and post office recurring deposit)");
    expect(fitTitle("SIP calculator | Free", "en")).toBe("SIP calculator for India | Free");
    expect(fitTitle("A title that already fits nicely | Free", "en")).toBe("A title that already fits nicely | Free");
  });
  it("pads short descriptions with a true line and leaves long ones alone", () => {
    expect(fitDescription("Short.", "en")).toBe("Short. By Kalpa Labs, Hyderabad. Works on your phone.");
    const long = "x".repeat(90);
    expect(fitDescription(long, "te")).toBe(long);
  });
  it("every calculator page title and description lands in range, English and Telugu", () => {
    for (const c of CALCS) for (const lang of ["en", "te"] as const) {
      const t = fitTitle(`${c.title[lang]} | ${lang === "en" ? "Free" : "ఉచితం"}`, lang);
      expect(inTitle(t), `${c.slug} ${lang} title ${t.length}: ${t}`).toBe(true);
      expect(inDesc(fitDescription(c.blurb[lang], lang)), `${c.slug} ${lang} description`).toBe(true);
    }
  });
  it("every kit page title and description lands in range", () => {
    for (const k of KITS) {
      expect(inTitle(fitTitle(`${k.name} | Google Sheets kit`, "en")), k.slug).toBe(true);
      expect(inDesc(fitDescription(k.short, "en")), k.slug).toBe(true);
    }
  });
});
