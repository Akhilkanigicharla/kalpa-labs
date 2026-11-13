// SEO checks 5 and 6 (00-hq/design/SEO-CHECKS.md): every page title 30–60 characters, every description 70–160.
// Base.astro runs every page through these, so new calculators and kits stay inside the limits.
type Lang = "en" | "te";
const REGION: Record<Lang, string> = { en: " for India", te: " (భారతదేశం)" };
const TAIL: Record<Lang, string> = { en: " By Kalpa Labs, Hyderabad. Works on your phone.", te: " Kalpa Labs, హైదరాబాద్. ఫోన్‌లో పని చేస్తుంది." };

export function fitTitle(title: string, lang: Lang): string {
  const cut = title.lastIndexOf(" | ");
  if (title.length > 60 && cut > 0) return title.slice(0, cut); // drop the " | Free" style suffix first
  if (title.length < 30 && cut > 0) return title.slice(0, cut) + REGION[lang] + title.slice(cut);
  return title;
}

export function fitDescription(d: string, lang: Lang): string {
  return d.length < 70 ? d + TAIL[lang] : d;
}
