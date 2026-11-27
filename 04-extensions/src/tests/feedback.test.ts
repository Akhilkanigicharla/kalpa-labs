import { describe, expect, it } from "vitest";
import { answerRating, FEEDBACK_FORM_URL, formLink, isFormUrl, RATE_DEFAULT, shouldAskRating, STORE_REVIEW_URL, UNINSTALL_FORM_URL } from "../lib/feedback";

const DAY = 864e5;

describe("form links", () => {
  it("accepts only https Google Forms links", () => {
    expect(isFormUrl("https://forms.gle/abc123")).toBe(true);
    expect(isFormUrl("https://docs.google.com/forms/d/e/1FAIpQ/viewform")).toBe(true);
    for (const bad of ["", "http://forms.gle/abc", "https://evil.com/forms/x", "https://docs.google.com/document/d/x", "javascript:alert(1)", "https://forms.gle.evil.com/x", "not a url 🚀"])
      expect(isFormUrl(bad), bad).toBe(false);
  });
  it("an empty or wrong link switches the feature off instead of breaking", () => {
    expect(formLink("")).toBeNull();
    expect(formLink("https://evil.com")).toBeNull();
    expect(formLink("https://forms.gle/abc")).toBe("https://forms.gle/abc");
  });
  it("shipped links are empty or real Google Forms, and the review link is our own store listing", () => {
    for (const u of [FEEDBACK_FORM_URL, UNINSTALL_FORM_URL]) expect(u === "" || isFormUrl(u)).toBe(true);
    expect(STORE_REVIEW_URL).toBe("https://chromewebstore.google.com/detail/kkdmhgljkdoclnifiegbiaklgjmnbfcc/reviews");
  });
});

describe("rating ask", () => {
  it("waits until Tab Lifeboat has helped 3 times", () => {
    expect(shouldAskRating({ ...RATE_DEFAULT, restores: 2 })).toBe(false);
    expect(shouldAskRating({ ...RATE_DEFAULT, restores: 3 })).toBe(true);
  });
  it("never asks again after rating", () => {
    const s = answerRating({ ...RATE_DEFAULT, restores: 5 }, "rate", 0);
    expect(shouldAskRating(s, 365 * DAY)).toBe(false);
  });
  it("'Not now' hides it for 30 days, and it asks at most twice", () => {
    let s = answerRating({ ...RATE_DEFAULT, restores: 9 }, "later", 0);
    expect(shouldAskRating(s, 29 * DAY)).toBe(false);
    expect(shouldAskRating(s, 30 * DAY)).toBe(true);
    s = answerRating(s, "later", 30 * DAY);
    expect(shouldAskRating(s, 400 * DAY)).toBe(false);
  });
});
