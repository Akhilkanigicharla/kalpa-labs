// Parent gate: a sum most 4 to 10 year olds cannot do quickly (two-digit x one-digit).
// It keeps small hands out of settings; it is not security.
export function makeChallenge(rand = Math.random) {
  const a = 12 + Math.floor(rand() * 18); // 12..29
  const b = 3 + Math.floor(rand() * 7);   // 3..9
  return { question: `${a} × ${b}`, spoken: `${a} times ${b}`, answer: a * b };
}

export function checkAnswer(challenge, input) {
  const s = String(input ?? '').trim();
  if (!/^\d{1,4}$/.test(s)) return false;
  return Number(s) === challenge.answer;
}
