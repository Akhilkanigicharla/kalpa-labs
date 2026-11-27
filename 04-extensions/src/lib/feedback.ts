// Feedback from real users (Akhil, 27 Nov 2026: "i want feedback from real humans what they need").
// Tab Lifeboat has no server and collects nothing on its own. Everything here is opt-in: the user opens a
// Google Form only if they click, and the uninstall form opens once when they remove the extension.
// Akhil makes the two forms in the business Gmail and pastes their links below (empty = feature switched off).

export const FEEDBACK_FORM_URL = "";   // "Tell us what you need" form, e.g. https://forms.gle/xxxx
export const UNINSTALL_FORM_URL = "";  // "Why did you remove Tab Lifeboat?" form
export const STORE_REVIEW_URL = "https://chromewebstore.google.com/detail/kkdmhgljkdoclnifiegbiaklgjmnbfcc/reviews";

export const RATE_AFTER_RESTORES = 3;      // ask only after Tab Lifeboat has really helped someone
export const RATE_SNOOZE_DAYS = 30;        // "Not now" hides it for a month
export const RATE_MAX_ASKS = 2;            // never more than twice in total

/** Only Google Forms links are allowed, so a typo can never send users somewhere else. */
export function isFormUrl(u: string): boolean {
  try {
    const x = new URL(u);
    return x.protocol === "https:" && (x.hostname === "forms.gle" || (x.hostname === "docs.google.com" && x.pathname.startsWith("/forms/")));
  } catch { return false; }
}

/** Form link to show, or null when Akhil has not set one yet. */
export function formLink(u: string): string | null { return u && isFormUrl(u) ? u : null; }

export type RateState = { restores: number; rated: boolean; asks: number; snoozedAt: number | null };
export const RATE_DEFAULT: RateState = { restores: 0, rated: false, asks: 0, snoozedAt: null };

/** Show "Rate Tab Lifeboat" only after a few real restores, never after rating, at most twice, a month apart. */
export function shouldAskRating(s: RateState, now = Date.now()): boolean {
  if (s.rated || s.asks >= RATE_MAX_ASKS || s.restores < RATE_AFTER_RESTORES) return false;
  return s.snoozedAt === null || now - s.snoozedAt >= RATE_SNOOZE_DAYS * 864e5;
}

/** State after the user clicks: "rate" (opens the store) or "later" (snooze a month). */
export function answerRating(s: RateState, a: "rate" | "later", now = Date.now()): RateState {
  return a === "rate" ? { ...s, rated: true, asks: s.asks + 1 } : { ...s, asks: s.asks + 1, snoozedAt: now };
}
