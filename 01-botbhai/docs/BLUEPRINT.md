# BotBhai blueprint: the real product, from the client's side (30 Oct 2026)

Akhil, 30 Oct: "for the client, what are we providing, do we follow standard policies, is there an app, how do agents and the dashboard talk, where are admin logins and credentials stored, how do we onboard clients with automation?" This file answers with what is **built today** (from the code) and what is **missing**, then the build items that close each gap. Business detail (prices, margin, sales) is in `OFFER.md`.

## 1. The pieces today (built, tested, not live)
| Piece | What it is | Where |
|---|---|---|
| Customer channels | WhatsApp Cloud API webhook, website chat widget, Telegram bot, browser voice | `core/functions/whatsapp.js`, `chat.js`, `telegram.js`, `web/widget.js` |
| Brain | One engine per business type (salon, gym, real estate, exam kits) + humanize layer (persona, Telugu/Hindi mirroring, empathy, hand-over) | `core/engine.js`, `core/humanize.js`, `setups/` |
| Data | Supabase Postgres: `clients`, `sessions`, `leads`, `messages`, `bookings` (capacity lock), `members`, `jobs`, `invoices`, `processed`, `rate_hits` | `supabase/schema.sql` |
| Owner screens | Dashboard (bookings, 30-day report, Excel), shared inbox (take over / hand back), billing (UPI QR invoices) | `web/dashboard.html`, `inbox.html`, `billing.html` |
| Automations | Reminders, day-close, Meta lead follow-up, ads guard, owner reports, Social Team (posts only after owner OK) | `core/functions/*.js`, `social/` |
| Secrets | Platform keys in Netlify env (set by Akhil). Each client's Meta token in **Supabase Vault**, read only by a server RPC (A51) | `_lib.js clientToken` |

## 2. Gaps a paying client would notice
1. **No real login.** The owner opens the dashboard with one long secret key (`dashboard_token`), stored as plain text in `clients`. No password reset, no staff accounts, no way to see who did what.
2. **No Kalpa admin console.** Adding a salon means hand-editing a JSON config and a database row.
3. **No self-serve onboarding.** No form that turns "services, prices, staff, hours" into a working bot.
4. **No app feel.** Pages work on a phone but are not installable, and there are no push alerts.
5. **Policies exist as drafts only.** Agreement, privacy notice and objections PDFs exist; no published Terms, DPA, acceptable-use, support/SLA, refund, data-retention and incident-response pages.
6. **Agent ↔ client loop is one-way.** n8n agents report to Kalpa (KL Tasks, CEO update); the salon only sees bot results, not what our agents did for them (posts drafted, reviews requested).

## 3. Target design
- **Logins (A131):** Supabase Auth with phone OTP or email magic link. Roles: `owner`, `staff` (inbox only), `kalpa_admin`. Row-level security on every table by `client_id`. `dashboard_token` kept only as a hashed, revocable backup key. An `audit_log` table records logins, takeovers, config changes and exports.
- **Credentials:** platform secrets in Netlify/GitHub/n8n credentials (set by Akhil, never in chat or code); per-client tokens (Meta, Telegram) in Supabase Vault; nothing secret in the browser; keys rotated on staff exit.
- **Kalpa admin console (A132):** list clients, health (last message, reminders sent, errors), create a client from an onboarding form, pause a bot, impersonate read-only for support (logged).
- **Onboarding automation (A133):** Telugu + English form → n8n checks it (prices numeric, hours valid, no personal data of customers) → creates the `clients` row and config → sends the owner a login invite → runs 10 test chats → owner taps "go live". Target: 20 minutes of the owner's time.
- **Owner app (A134):** the dashboard + inbox as an installable PWA (home-screen icon, offline shell, Web Push for hand-overs), Telugu view, daily summary.
- **Policy pack (A135):** Terms of Service, Data Processing Agreement (salon = fiduciary, Kalpa = processor), Privacy Notice for the salon's customers, Acceptable Use (no spam, no marketing without opt-in), Support & SLA (hours, response times), Refund, Data retention (messages 180 days), Incident response (notify within 72 h). Drafted by agents, checked by Claude, read by a lawyer/CA before the first paid client (C23).
- **Agent ↔ client loop (A136):** a `client_activity` feed in the owner app: "Kavi drafted 3 posts, waiting for your OK", "Vigil checked your prices", "12 reminders sent today". Agents write to it through one server function with a per-agent key; the owner approves from the app.

## 4. Who does what (the workforce)
- **Claude sessions:** code, tests, security, verification (A131–A136).
- **n8n agents (free models):** research, policy drafts, onboarding copy, sales kit, councils; 80+ BotBhai jobs queued 30 Oct (KL Tasks, stream b1).
- **Registry:** salon team, platform dev/test/quality/ops teams already defined in `00-hq/agents/registry.js`.
- **Akhil:** accounts and keys, legal sign-off, salon visits, the go/no-go on price.

## 5. Order of work (money sprint, track 3)
A87 (bot quality) → A131 (logins + roles) → A133 (onboarding automation) → A134 (owner app) → A132 (admin console) → A135 (policies) → A136 (activity feed) → first pilot.
