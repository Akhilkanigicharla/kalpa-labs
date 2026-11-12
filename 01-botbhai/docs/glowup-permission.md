# Website glow-up: owner permission + privacy notice (form v1)

Status: **draft, needs Akhil/lawyer check before first use.** Based on free-model draft K058, checked by Claude 12 Nov 2026:
removed an invented contact email (`privacy@botbhai.in` does not exist), removed claims we have not tested ("lightning-fast",
"hosting included"), added the clean-room limits the build tool enforces (`01-botbhai/botbhai/glowup/glowup.py`).

The tool will not build a page until `owner.json` has `permission` with `signed_by`, `date` (YYYY-MM-DD),
`form_version: "glowup-permission v1"` and `owns_content: true`. If the owner withdraws, set `withdrawn: true`;
the tool then refuses to build and the owner's files are deleted.

---

## Permission to rebuild my website

Business name: ____________________ Website now: ____________________

I am the owner of this business, or I am allowed to sign for it. I give Kalpa Labs (BotBhai) permission to:

1. look at my current website, only to take screenshots of it at phone, tablet and computer size for a before/after comparison;
2. use **only** the text, photos and logo that I send or that are on my own website, to build a new page for my business.

I confirm that I own these texts, photos and logo, or have the right to use them. I will tell Kalpa Labs if any of them belong to someone else.

Kalpa Labs will not copy anything from other businesses' websites and will not use my photos for anything else without asking me.

I can withdraw this permission at any time by sending a WhatsApp message or email to Kalpa Labs. After that, Kalpa Labs stops work and deletes my files within 30 days.

Signed: ____________________ Name: ____________________ Date: ____________

## Privacy notice (DPDP Act 2023)

- **What we collect:** your name, phone/WhatsApp number, and the text, photos and logo you share for your website.
- **Why:** only to build and update your new web page. Nothing is sold or shared for advertising.
- **Photos:** before use, we remove hidden location (GPS) and camera details from every photo.
- **How long:** while we work on your page and up to 30 days after you stop the service, then deleted, unless you ask us to keep it.
- **Your rights:** you can ask to see, correct or delete your data, or withdraw consent, at: ____________ (Akhil to fill a real contact).

## WhatsApp offer line (opt-in customers only, no price claims)

English: "Your website can look good on phones too. With your permission, we rebuild it from your own text and photos and show you a before/after first. Reply YES if you'd like to see it."

Tenglish: "Mee website phone lo kuda neat ga kanipinchali ante, mee permission tho, mee own text and photos tho kotha page chesi, before/after mundu chupistham. Chudalante YES ani reply cheyandi."
