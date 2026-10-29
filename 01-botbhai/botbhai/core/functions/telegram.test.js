// A130: BotBhai on Telegram. Fake Supabase (+ Meta) from _fake.js; Telegram's Bot API is faked here.
const assert = require("assert");
process.env.NO_DELAY = "1";
const CID = "11111111-2222-3333-4444-555555555555";
const { store, graph } = require("./_fake.js")({ clients: [{ id: CID, name: "Glow Studio", niche: "salon", phone_number_id: "PNID", owner_whatsapp: "919000000000", active: true, config: { capacity: 1 }, dashboard_token: "abcdefgh" + "x".repeat(28) }] });
Object.assign(process.env, { TELEGRAM_BOT_TOKEN: "123:abc", TELEGRAM_WEBHOOK_SECRET: "s3cret-s3cret-s3cret" });
const tgSent = []; const fakeFetch = global.fetch;
global.fetch = async (url, opts = {}) => {
  if (String(url).startsWith("https://api.telegram.org/bot123:abc/")) {
    tgSent.push({ method: url.split("/").pop(), body: JSON.parse(opts.body) });
    return { ok: true, status: 200, json: async () => ({ ok: true, result: {} }) };
  }
  return fakeFetch(url, opts);
};
const { handler, _keyboard, _toHtml } = require("./telegram.js");
let uid = 0;
const post = (update, { secret = "s3cret-s3cret-s3cret", client = CID } = {}) => handler({ httpMethod: "POST", headers: { "x-telegram-bot-api-secret-token": secret }, queryStringParameters: { client }, body: JSON.stringify(Object.assign({ update_id: ++uid }, update)) });
const chat = { id: 777, type: "private", first_name: "Ravi" };
const say = (text, c = chat) => post({ message: { message_id: uid, chat: c, text } });
const tap = (data, c = chat) => post({ callback_query: { id: "cb" + uid, data: "t:" + data, message: { message_id: uid, chat: c } } });
const toCustomer = () => tgSent.filter((s) => s.method === "sendMessage" && s.body.chat_id === 777);
const last = () => toCustomer().slice(-1)[0].body;

(async () => {
  // security: wrong/missing secret, bad client id, GET
  assert.strictEqual((await post({ message: { chat, text: "hi" } }, { secret: "nope" })).statusCode, 401);
  assert.strictEqual((await post({ message: { chat, text: "hi" } }, { client: "x" })).statusCode, 400);
  assert.strictEqual((await handler({ httpMethod: "GET", headers: {} })).statusCode, 405);
  assert.strictEqual(tgSent.length, 0, "nothing sent on rejected calls");
  console.log("  ✓ rejects bad secret, bad client id and non-POST");

  // /start greets with the menu as buttons
  await say("/start");
  assert.ok(toCustomer().length >= 1, "greeting sent");
  assert.ok(toCustomer().some((m) => m.body.reply_markup && m.body.reply_markup.inline_keyboard.length), "menu has buttons");
  console.log("  ✓ /start → greeting with tap buttons");

  // same update twice (Telegram retry) → handled once
  const before = toCustomer().length;
  const dup = { update_id: 9999, message: { message_id: 1, chat, text: "price" } };
  await handler({ httpMethod: "POST", headers: { "x-telegram-bot-api-secret-token": "s3cret-s3cret-s3cret" }, queryStringParameters: { client: CID }, body: JSON.stringify(dup) });
  const once = toCustomer().length;
  await handler({ httpMethod: "POST", headers: { "x-telegram-bot-api-secret-token": "s3cret-s3cret-s3cret" }, queryStringParameters: { client: CID }, body: JSON.stringify(dup) });
  assert.ok(once > before && toCustomer().length === once, "retry ignored");
  console.log("  ✓ Telegram retries are not answered twice");

  // a full booking by taps ends in a confirmed booking row + owner alert (WhatsApp fallback: no owner Telegram yet)
  await say("book");
  for (let i = 0; i < 12 && !store.bookings.length; i++) {
    const kb = last().reply_markup; 
    if (kb) await tap(kb.inline_keyboard[0][0].callback_data.slice(2)); else { const q = last().text; await say(/day/i.test(q) ? "tomorrow" : /name/i.test(q) ? "Ravi" : /time|slot/i.test(q) ? "11am" : "yes"); }
  }
  assert.strictEqual(store.bookings.length, 1, "booking saved");
  assert.strictEqual(store.bookings[0].contact, "tg:777");
  assert.strictEqual(store.bookings[0].source, "telegram");
  assert.ok(graph.sent.some((m) => m.to === "919000000000"), "owner alerted (WhatsApp fallback)");
  assert.ok(store.messages.some((m) => m.contact === "tg:777" && m.direction === "in"), "inbox has the chat");
  console.log("  ✓ booking by taps → calendar row, inbox messages, owner alert");

  // owner links Telegram with the code; next alerts go to the owner's Telegram chat
  const owner = { id: 555, type: "private", first_name: "Owner" };
  await say("/owner wrongcod", owner);
  assert.ok(!store.clients[0].config.owner_telegram_chat_id, "wrong code ignored");
  await say("/owner abcdefgh", owner);
  assert.strictEqual(store.clients[0].config.owner_telegram_chat_id, 555);
  console.log("  ✓ /owner <code> links the owner's chat; wrong code does nothing");

  // groups are ignored
  const n = tgSent.length; await say("hi", { id: -100, type: "group" }); assert.strictEqual(tgSent.length, n);
  console.log("  ✓ group chats are ignored");

  // long options don't break Telegram's 64-byte callback limit
  const kb = _keyboard(["Short", "x".repeat(80)]);
  assert.strictEqual(kb.inline_keyboard.length, 1);
  assert.strictEqual(_toHtml("*1.* Hair <spa> & 5*"), "<b>1.</b> Hair &lt;spa&gt; &amp; 5*");
  console.log("  ✓ WhatsApp bold becomes safe Telegram HTML; long options are dropped");
  console.log("telegram tests passed");
})().catch((e) => { console.error(e); process.exit(1); });
