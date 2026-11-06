"""Tests for the agents' lesson memory (A171). Run: python3 00-hq/agents/test_memory.py"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import memory as M  # noqa: E402


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_store_and_recall_by_topic(self):
        M.store("b6", "K1", "Never quote API prices without a source; mark them UNVERIFIED.", self.root)
        M.store("b6", "K2", "Telugu replies must use Telugu script, not English letters.", self.root)
        got = M.recall("b6", "pilot plan with OpenAI API prices per 1,000 calls", root=self.root)
        self.assertTrue(got and "prices" in got[0])

    def test_worlds_are_separate(self):
        M.store("b6", "K1", "Mark unknown prices UNVERIFIED.", self.root)
        self.assertEqual(M.recall("b3", "prices", root=self.root), [])

    def test_limit_and_dedupe(self):
        for i in range(8):
            M.store("hq", f"K{i}", f"lesson about tests number {i}", self.root)
        M.store("hq", "K9", "lesson about tests number 1", self.root)
        got = M.recall("hq", "tests", k=5, root=self.root)
        self.assertEqual(len(got), 5)
        self.assertEqual(len(set(got)), 5)

    def test_personal_data_is_scrubbed(self):
        M.store("b1", "K1", "Do not print ravi@example.com or +91 98765 43210 in drafts.", self.root)
        text = open(os.path.join(self.root, M.DIR, "b1.jsonl"), encoding="utf-8").read()
        self.assertNotIn("ravi@example.com", text)
        self.assertNotIn("98765", text)

    def test_lesson_from_verdict(self):
        self.assertEqual(M.lesson_from_verdict("PASS"), "")
        self.assertIn("UNVERIFIED", M.lesson_from_verdict("FIX:\n- mark the Plivo rate UNVERIFIED\n- shorter"))

    def test_empty_recall_when_no_file(self):
        self.assertEqual(M.recall("b7", "anything", root=self.root), [])


if __name__ == "__main__":
    unittest.main()
