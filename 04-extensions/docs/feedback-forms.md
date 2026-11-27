# Tab Lifeboat feedback forms (Akhil makes these, ~10 min on a laptop)

Account: business Gmail **aakhiil51458@gmail.com** → https://forms.google.com → Blank form.
Settings for both forms: Responses → **Collect email addresses: Do not collect**; "Limit to 1 response": OFF
(no Google sign-in needed). Then Send → link icon → tick "Shorten URL" → copy the `forms.gle/...` link.

## Form 1: "Tab Lifeboat · Tell us what you need"
1. What do you mainly use Tab Lifeboat for? (Multiple choice) Saving tabs before closing Chrome · Recovering tabs after a crash or update · Moving from OneTab / Session Buddy · Keeping research or work projects · Other
2. What is the ONE thing you wish Tab Lifeboat did? (Paragraph, required)
3. Has anything been confusing or broken? (Paragraph)
4. How likely are you to recommend it to a friend? (Linear scale 0–10)
5. Your email, only if you want a reply (Short answer, optional)

## Form 2: "Tab Lifeboat · Why did you remove it?"
1. Why did you remove Tab Lifeboat? (Checkboxes) It didn't save or restore my tabs · Hard to understand · I only needed it once · I use another extension (which one? → Other) · Too many permissions · Other
2. What would have made you keep it? (Paragraph)
3. Your email, only if you want a reply (Short answer, optional)

## Then
Send both `forms.gle` links to Claude. Claude puts them in `src/lib/feedback.ts` (the tests refuse any link that is
not a Google Forms link), rebuilds version 0.2.0 and gives you the zip to upload in the Web Store dashboard.
Answers land in each form's **Responses** tab (or a linked Google Sheet).
