/*
 * BotBhai slot engine — Kalpa Labs                                           v1.0
 * Which times can a customer book on a given day? Pure JavaScript, no dependencies, IST only.
 *
 * Algorithm ported from cal.com / cal.diy (MIT, © 2020-present Cal.com, Inc.):
 *   packages/features/schedules/lib/date-ranges.ts  → weekly hours become ranges per day; a date
 *     override REPLACES that day's hours; an empty override closes the day; subtract() for breaks.
 *   packages/features/schedules/lib/slots.ts        → start at max(range start, now + notice), round up
 *     to the interval in local time, step by interval, keep a slot only while start + length ≤ range end.
 *   availability/lib/getAggregatedAvailability     → "any stylist" = a slot is free if any staff member is free.
 *   date-range-utils/mergeOverlappingDateRanges.ts → merge overlapping ranges.
 * See the NOTICE section in ../README.md.
 *
 * Minutes since IST midnight everywhere (600 = 10:00 AM). Days are "YYYY-MM-DD" IST calendar dates.
 *
 * Config (all optional; a setup without `schedule` behaves exactly like BotBhai v3.0):
 *   closed_weekdays: [0]                  // 0 = Sunday (legacy key, still read)
 *   holidays: [{ date: "2026-11-08", name: "Diwali" }]
 *   lead_minutes: 30, capacity: 3        // legacy keys, still read
 *   schedule: {
 *     hours: { default: [["10:00", "21:00"]], sun: [["11:00", "18:00"]], tue: "closed" },
 *     weekly_off: [2],                    // same as closed_weekdays
 *     breaks: [["14:00", "15:00"]],       // every working day
 *     special: [{ date: "2026-10-20", hours: [["10:00", "14:00"]], name: "Dhanteras" },
 *               { date: "2026-10-21", closed: true, name: "staff outing" }],
 *     closing_today: { date: "2026-10-12", at: "18:00" },   // or { date, closed: true }
 *     interval: 30,                       // grid for generated slots
 *     default_minutes: 30,                // service length when the catalog doesn't say
 *     durations: { "Keratin treatment": 120 },              // or catalog item { minutes: 120 }
 *     staff: [{ name: "Ravi", off_days: [3], off_dates: ["2026-10-14"], hours: [["12:00", "21:00"]] }],
 *   }
 * Bookings ("busy"): [{ date_iso, slot: "4:00 PM", service?, minutes?, staff?, blocked? }]
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BotBhaiSlots = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const IST_MS = 330 * 60000;
  const DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  // ---------------------------------------------------------------- small helpers
  // "10:00", "10:00 AM", "7 pm", "19:30", 600 → minutes since midnight (null if unreadable)
  function toMin(x) {
    if (typeof x === "number" && isFinite(x)) return x;
    const m = String(x || "").trim().match(/^(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?$/i);
    if (!m) return null;
    let h = +m[1]; const mm = m[2] ? +m[2] : 0; const ap = m[3] ? m[3][0].toLowerCase() : null;
    if (mm > 59 || h > 24 || (ap && (h < 1 || h > 12))) return null;
    if (ap) h = (h % 12) + (ap === "p" ? 12 : 0);
    return h * 60 + mm;
  }
  // 960 → "4:00 PM" (same shape as BotBhai slot labels)
  function label(min) {
    const h = Math.floor(min / 60) % 24; const mm = min % 60;
    return `${((h + 11) % 12) + 1}:${String(mm).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
  }
  function weekday(iso) { return new Date(iso + "T00:00:00Z").getUTCDay(); }
  function istIso(now) { return new Date(new Date(now).getTime() + IST_MS).toISOString().slice(0, 10); }
  function istMin(now) { const z = new Date(new Date(now).getTime() + IST_MS); return z.getUTCHours() * 60 + z.getUTCMinutes(); }
  function prettyDay(iso) { const d = new Date(iso + "T00:00:00Z"); const w = DAYS[d.getUTCDay()]; return `${w[0].toUpperCase()}${w.slice(1, 3)}, ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; }
  function plural(day) { return DAYS[day][0].toUpperCase() + DAYS[day].slice(1) + "s"; }

  // [["10:00","14:00"], "16:00-21:00", { from, to }] → sorted, merged [{ start, end }]
  function ranges(list) {
    if (list === undefined || list === null) return null;
    if (list === "closed" || list === false) return [];
    const arr = Array.isArray(list) && list.length === 2 && !Array.isArray(list[0]) && typeof list[0] !== "object" && !/-/.test(String(list[0])) ? [list] : [].concat(list);
    const out = [];
    for (const r of arr) {
      let a, b;
      if (Array.isArray(r)) { a = r[0]; b = r[1]; }
      else if (r && typeof r === "object") { a = r.from !== undefined ? r.from : r.start; b = r.to !== undefined ? r.to : r.end; }
      else { const p = String(r).split(/\s*[-–]\s*/); a = p[0]; b = p[1]; }
      const s = toMin(a); let e = toMin(b);
      if (s === null || e === null) continue;
      if (e <= s) e += 24 * 60; // "18:00-00:00": open till midnight
      out.push({ start: s, end: e });
    }
    return merge(out);
  }
  // cal.com mergeOverlappingDateRanges (MIT)
  function merge(list) {
    const sorted = list.filter((r) => r.end > r.start).sort((a, b) => a.start - b.start);
    const out = [];
    for (const r of sorted) {
      const last = out[out.length - 1];
      if (last && r.start <= last.end) last.end = Math.max(last.end, r.end);
      else out.push({ start: r.start, end: r.end });
    }
    return out;
  }
  // cal.com subtract (MIT): source ranges minus excluded ranges
  function subtract(source, excluded) {
    const ex = merge(excluded || []); const out = [];
    for (const { start, end } of source) {
      let cur = start;
      for (const x of ex) {
        if (x.start >= end) break;
        if (x.end <= cur) continue;
        if (x.start > cur) out.push({ start: cur, end: x.start });
        cur = Math.max(cur, x.end);
      }
      if (end > cur) out.push({ start: cur, end });
    }
    return out;
  }
  // cal.com intersect (MIT), for two lists
  function intersect(a, b) {
    const out = []; let i = 0, j = 0;
    while (i < a.length && j < b.length) {
      const s = Math.max(a[i].start, b[j].start), e = Math.min(a[i].end, b[j].end);
      if (s < e) out.push({ start: s, end: e });
      if (a[i].end < b[j].end) i++; else j++;
    }
    return out;
  }

  // ---------------------------------------------------------------- config
  function schedule(cfg) {
    cfg = cfg || {}; const s = cfg.schedule || {};
    const hours = s.hours || null; const weekly = {};
    if (hours) {
      const def = hours.default !== undefined ? hours.default : (Array.isArray(hours) || typeof hours === "string" ? hours : undefined);
      for (let d = 0; d < 7; d++) {
        const own = !Array.isArray(hours) && typeof hours === "object" ? (hours[KEYS[d]] !== undefined ? hours[KEYS[d]] : hours[DAYS[d]]) : undefined;
        weekly[d] = ranges(own !== undefined ? own : def);
      }
    }
    const durations = Object.assign({}, s.durations || {});
    for (const c of cfg.catalog || []) if (c && c.minutes && durations[c.name] === undefined) durations[c.name] = +c.minutes;
    return {
      structured: !!hours,
      weekly,
      off: [].concat(s.weekly_off || [], cfg.closed_weekdays || []).map(Number),
      breaks: ranges(s.breaks) || [],
      holidays: [].concat(s.holidays || [], cfg.holidays || []),
      special: [].concat(s.special || []),
      closing: [].concat(s.closing_today || []),
      interval: Math.max(5, +s.interval || 30),
      lead: cfg.lead_minutes !== undefined ? +cfg.lead_minutes : s.lead_minutes !== undefined ? +s.lead_minutes : 30,
      defaultMinutes: +s.default_minutes || 0,
      durations,
      staff: Array.isArray(s.staff) && s.staff.length ? s.staff : null,
      capacity: cfg.capacity || s.capacity || Infinity,
    };
  }
  function durationOf(sch, service, explicit) {
    if (explicit) return +explicit;
    if (service && sch.durations[service]) return sch.durations[service];
    return sch.defaultMinutes || (sch.structured ? sch.interval : 1); // legacy: a booking only blocks its own start time
  }

  // Working ranges of the business on one day + why it's closed. ranges === null means "no hours set" (legacy).
  function day(cfgOrSch, iso) {
    const sch = cfgOrSch && cfgOrSch.weekly ? cfgOrSch : schedule(cfgOrSch);
    const wd = weekday(iso);
    const hol = sch.holidays.find((h) => h && h.date === iso);
    if (hol) return { open: false, ranges: [], reason: `we're closed for ${hol.name || "a holiday"}` };
    const sp = sch.special.filter((x) => x && x.date === iso);
    let list;
    if (sp.length) { // date override replaces the weekly hours for that day (cal.com rule)
      const shut = sp.find((x) => x.closed);
      list = shut ? [] : merge([].concat(...sp.map((x) => ranges(x.hours) || [])));
      if (!list.length) { const n = (shut || sp[0]).name; return { open: false, ranges: [], reason: `we're closed on ${prettyDay(iso)}${n ? ` (${n})` : ""}` }; }
    } else {
      if (sch.off.includes(wd)) return { open: false, ranges: [], reason: `we're closed on ${plural(wd)}` };
      list = sch.structured ? sch.weekly[wd] : null;
      if (list && !list.length) return { open: false, ranges: [], reason: `we're closed on ${plural(wd)}` };
    }
    let note = null;
    const cl = sch.closing.find((x) => x && x.date === iso);
    if (cl) {
      if (cl.closed) return { open: false, ranges: [], reason: "we're closed today", closingToday: true };
      const at = toMin(cl.at);
      if (at !== null) { list = list ? subtract(list, [{ start: at, end: 48 * 60 }]) : [{ start: 0, end: at }]; note = `closing early today at ${label(at)}`; }
      if (list && !list.length) return { open: false, ranges: [], reason: `we're ${note || "closed today"}`, closingToday: true };
    }
    if (list && sch.breaks.length) list = subtract(list, sch.breaks);
    return { open: true, ranges: list, reason: null, note, closingToday: !!cl };
  }
  function closedReason(cfgOrSch, iso) { return day(cfgOrSch, iso).reason; }

  function staffRanges(sch, member, iso, base) {
    const wd = weekday(iso);
    if ((member.off_days || []).map(Number).includes(wd) || (member.off_dates || []).includes(iso)) return [];
    let own = member.hours !== undefined ? ranges(member.hours) : null;
    if (own && member.hours && typeof member.hours === "object" && !Array.isArray(member.hours)) own = ranges(member.hours[KEYS[wd]] !== undefined ? member.hours[KEYS[wd]] : member.hours.default);
    if (base === null) return own; // legacy (no business hours): staff hours alone, or unbounded
    return own ? intersect(base, own) : base;
  }
  const fits = (list, s, e) => list === null || list.some((r) => r.start <= s && e <= r.end);
  // Most bookings running at the same moment inside [s, e) (sweep line)
  function peak(list, s, e) {
    const pts = []; for (const b of list) { const a = Math.max(b.start, s), z = Math.min(b.end, e); if (a < z) { pts.push([a, 1]); pts.push([z, -1]); } }
    pts.sort((x, y) => x[0] - y[0] || x[1] - y[1]); let cur = 0, max = 0; for (const p of pts) { cur += p[1]; if (cur > max) max = cur; } return max;
  }

  /*
   * free({ cfg | schedule, date_iso, now, busy, service, minutes, labels })
   *   labels: fixed start times from the setup ("11:00 AM", ...). Leave out to generate a grid from the hours.
   * → [{ label, start, end, free, staff: [names free at that time] }] in time order; only bookable ones.
   */
  function free(o) {
    const sch = o.schedule || schedule(o.cfg);
    const iso = o.date_iso; const info = day(sch, iso);
    if (!info.open) return [];
    const dur = durationOf(sch, o.service, o.minutes);
    const today = o.now ? istIso(o.now) === iso : false;
    const earliest = today ? istMin(o.now) + sch.lead : -Infinity;
    // candidate start times
    let starts = [];
    if (o.labels && o.labels.length) starts = o.labels.map((l) => ({ label: l, start: toMin(l) }));
    else if (info.ranges) {
      const step = sch.interval;
      for (const r of info.ranges) {
        let s = Math.max(r.start, earliest);
        if (s % step) s = Math.ceil(s / step) * step; // round up to the grid, in IST (cal.com rule)
        for (; s + dur <= r.end; s += step) starts.push({ label: label(s), start: s });
      }
    }
    // bookings on this day as intervals
    const busy = (o.busy || []).filter((b) => b && b.date_iso === iso).map((b) => {
      const st = b.start !== undefined ? +b.start : toMin(b.slot);
      return { start: st, end: st + durationOf(sch, b.service, b.minutes), staff: b.staff || null, blocked: !!b.blocked, slot: b.slot };
    }).filter((b) => b.start !== null && !isNaN(b.start));
    const out = []; const seen = new Set();
    for (const c of starts) {
      if (c.start === null) { // a label that isn't a time ("Morning batch"): count same-label bookings only
        const n = sch.capacity - (o.busy || []).filter((b) => b && b.date_iso === iso && b.slot === c.label).length;
        if (n > 0) out.push({ label: c.label, start: null, end: null, free: n, staff: [] }); continue;
      }
      if (seen.has(c.label)) continue; seen.add(c.label);
      const s = c.start, e = s + dur;
      if (s < earliest) continue;
      if (!fits(info.ranges, s, e)) continue;
      if (busy.some((b) => b.blocked && (b.slot === c.label || b.start === s))) continue;
      const over = busy.filter((b) => b.start < e && s < b.end);
      let n, names = [];
      if (sch.staff) {
        const unassigned = over.filter((b) => !b.staff || !sch.staff.some((m) => m.name === b.staff));
        names = sch.staff.filter((m) => fits(staffRanges(sch, m, iso, info.ranges), s, e) && !over.some((b) => b.staff === m.name)).map((m) => m.name);
        n = names.length - peak(unassigned, s, e);
      } else n = sch.capacity - peak(over, s, e);
      if (n > 0) out.push({ label: c.label, start: s, end: e, free: n, staff: names });
    }
    return out.sort((a, b) => (a.start === null || b.start === null ? 0 : a.start - b.start));
  }

  // Owner tells the bot "closing early today at 6 pm" / "closed today" → a closing_today entry (or null).
  function parseClosing(text, now) {
    const t = String(text || "").toLowerCase();
    if (!/\b(clos(e|ed|ing)|shut|band|holiday|leave)\b/.test(t) || !/\b(today|aaj|ivala|ee roju|now|early)\b/.test(t)) return null;
    const date = istIso(now || new Date());
    const m = t.match(/\b(?:at|by|@)?\s*(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?)\b(?!\s*(?:min|minutes|hrs|hours))/);
    const at = m ? toMin(m[1].replace(/\s+/g, " ")) : null;
    if (at !== null && /early|at|by|@/.test(t)) return { date, at: label(at < 12 * 60 && !/am/.test(m[1]) ? at + 12 * 60 : at) };
    return { date, closed: true };
  }

  return { toMin, label, ranges, merge, subtract, intersect, schedule, day, closedReason, free, durationOf, parseClosing, istIso, istMin, version: "1.0.0" };
});
