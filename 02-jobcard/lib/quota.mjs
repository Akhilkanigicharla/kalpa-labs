// Monthly limits per plan (PLAN.md §2). Over-quota minutes are not sold in months 1–3: the bot just says so.
export const PLANS = {
  free: { voiceMinutes: 20, jobCards: 10 },
  pro: { voiceMinutes: 150, jobCards: Infinity },
  team: { voiceMinutes: 400, jobCards: Infinity },
};

/** IST month start, YYYY-MM-01 (usage_minutes.month). */
export const istMonth = (now = Date.now()) => new Date(Number(now) + 330 * 60000).toISOString().slice(0, 8) + "01";

/** Where a technician stands this month. `blocked` = no more voice notes until the 1st (or an upgrade). */
export function voiceQuota(plan, usedSeconds) {
  const p = PLANS[plan] || PLANS.free; const limit = p.voiceMinutes * 60; const used = Math.max(0, Number(usedSeconds) || 0);
  return { limitSeconds: limit, usedSeconds: used, leftSeconds: Math.max(0, limit - used), blocked: used >= limit, warn: used < limit && used >= limit * 0.8 };
}

export function cardQuota(plan, cardsThisMonth) {
  const p = PLANS[plan] || PLANS.free; const used = Math.max(0, Number(cardsThisMonth) || 0);
  return { limit: p.jobCards, used, blocked: used >= p.jobCards };
}
