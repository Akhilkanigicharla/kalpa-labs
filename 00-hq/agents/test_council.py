import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import council

ENV = {"GROQ_API_KEY": "x", "GEMINI_API_KEY": "y", "KL_RETRY_WAIT": "0"}


def fake(stances, chair="Verdict: run a 1-week test."):
    """A fake model endpoint: seat replies follow `stances` in call order, then the chair."""
    calls = []

    def post(url, hdr, pay):
        calls.append(pay)
        sys_msg = pay["messages"][0]["content"]
        if "You chair" in sys_msg:
            return {"choices": [{"message": {"content": chair}}]}
        st = stances[(len(calls) - 1) % len(stances)]
        return {"choices": [{"message": {"content": "<think>hidden</think>" + json.dumps(
            {"stance": st, "score": 7, "why": f"because {st}", "cheapest_test": "ask 5 salons", "kill_if": "0 of 5 reply"})}}]}
    post.calls = calls
    return post


class Council(unittest.TestCase):
    def test_three_rounds_and_vote_counted_in_code(self):
        post = fake(["yes", "yes", "no", "yes", "change", "yes", "no"])
        res = council.run("Sell BotBhai to gyms?", ENV, post)
        self.assertEqual(len(post.calls), 15)  # 7 + 7 + chair
        self.assertEqual(res["majority"], "yes")
        self.assertEqual(sum(res["votes"].values()), 7)
        self.assertTrue(all(r["seat"] != "" for r in res["round2"]))
        self.assertEqual({r["seat"] for r in res["minority"]}, {s for s, _ in council.SEATS} - {r["seat"] for r in res["round2"] if r["stance"] == "yes"})

    def test_unanimous_round_one_triggers_devils_advocate(self):
        post = fake(["yes"])
        res = council.run("x", ENV, post)
        self.assertTrue(res["unanimous_r1"])
        risk_r2 = [c for c in post.calls[7:14] if "Cash & risk seat" in c["messages"][0]["content"]][0]
        self.assertIn("strongest case for the best alternative", risk_r2["messages"][1]["content"])

    def test_round_two_is_anonymous(self):
        post = fake(["yes", "no"])
        council.run("x", ENV, post)
        r2_user = post.calls[7]["messages"][1]["content"]
        self.assertIn("Seat A:", r2_user)
        for seat, _ in council.SEATS[1:]:
            self.assertNotIn(f"- {seat}:", r2_user)

    def test_seats_start_on_different_models(self):
        firsts = {council.models_for(i)[0][2] for i in range(len(council.SEATS))}
        self.assertGreaterEqual(len(firsts), 4)

    def test_parse_is_safe_with_bad_replies(self):
        self.assertEqual(council.parse("no json, I'd change it")["stance"], "change")
        r = council.parse('{"stance":"MAYBE","score":"99"}')
        self.assertEqual((r["stance"], r["score"]), ("change", 10))
        self.assertEqual(council.parse("")["score"], 5)

    def test_no_keys_still_writes_honest_report(self):
        res = council.run("x", {}, fake(["yes"]))
        self.assertEqual(res["votes"], {})
        md = council.to_md(res, "2026-11-08 18:00 IST")
        self.assertIn("Chair did not answer", md)

    def test_markdown_has_vote_minority_and_credit(self):
        res = council.run("Price kits at Rs 99?", ENV, fake(["yes", "no", "yes", "yes", "yes", "change", "yes"]))
        md = council.to_md(res, "2026-11-08 18:00 IST")
        for s in ("**Vote:**", "Minority report", "roast-room (MIT)", "| Seat | Stance |", "Cheapest tests"):
            self.assertIn(s, md)
        self.assertNotIn("<think>", md)

    def test_c_item_lookup(self):
        txt = council.c_item("C19")
        self.assertTrue(len(txt) > 10)


if __name__ == "__main__":
    unittest.main()
