import datetime as dt, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import live_status as ls

T = dt.datetime(2026, 11, 8, 10, 0, tzinfo=dt.timezone.utc)  # 15:30 IST


def repo(tasks, log=None):
    d = Path(tempfile.mkdtemp())
    (d / "00-hq/tasks").mkdir(parents=True)
    (d / "00-hq/log").mkdir(parents=True)
    for room, items in tasks.items():
        (d / f"00-hq/tasks/{room}.json").write_text(json.dumps(items))
    if log:
        (d / "00-hq/log/2026-11-08.md").write_text(log)
    return d


class LiveStatus(unittest.TestCase):
    def test_open_job_beats_newer_finished_job(self):
        rows = ls.worker_rows({"b1": [
            {"owner": "Chitti", "status": "review", "updated": "2026-11-07T10:00:00Z", "title": "old"},
            {"owner": "Chitti", "status": "todo", "updated": "2026-11-01T10:00:00Z", "title": "new job"}]})
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["state"], rows[0]["task"]), ("queued", "new job"))

    def test_running_agents_turn_queued_into_working(self):
        rows = ls.worker_rows({"hq": [{"owner": "Scout", "status": "todo", "title": "x"}]}, agents_running=True)
        self.assertEqual(rows[0]["state"], "working")

    def test_states_mapped_and_one_robot_per_room_owner(self):
        rows = ls.worker_rows({"b1": [{"owner": "Kavi", "status": "rejected", "updated": "a"}],
                               "b3": [{"owner": "Kavi", "status": "review", "updated": "b"}]})
        self.assertEqual({(r["room"], r["state"]) for r in rows}, {("b1", "redo"), ("b3", "needs review")})

    def test_claude_working_only_when_log_is_fresh(self):
        d = repo({}, "# 2026-11-08\n\n## 15:10 Live rooms for the CEO dashboard\n- x\n")
        self.assertEqual(ls.claude_row(d, T)["state"], "working")
        self.assertEqual(ls.claude_row(d, T + dt.timedelta(hours=2))["state"], "idle")
        self.assertEqual(ls.claude_row(d, T)["task"], "Live rooms for the CEO dashboard")

    def test_runs_latest_per_workflow_and_room(self):
        runs = ls.run_rows([
            {"name": "Backtest", "workflow_id": 1, "status": "completed", "conclusion": "success"},
            {"name": "Backtest", "workflow_id": 1, "status": "completed", "conclusion": "failure"},
            {"name": "Agents", "workflow_id": 2, "status": "in_progress"}])
        self.assertEqual([(r["workflow"], r["room"], r["conclusion"]) for r in runs],
                         [("Backtest", "b7", "success"), ("Agents", "hq", "")])

    def test_sql_escapes_quotes_and_replaces_tables(self):
        sql = ls.to_sql([{"id": "b1:x", "name": "O'Neil", "room": "b1", "team": "t", "runs_as": "r",
                          "state": "idle", "task": "it's", "detail": "", "updated_at": ""}], [], {"refreshed_at": "z"})
        self.assertTrue(sql.startswith("DELETE FROM agents_live;"))
        self.assertIn("'O''Neil'", sql)
        self.assertIn("'it''s'", sql)

    def test_build_has_claude_vigil_and_meta(self):
        d = repo({"b2": [{"owner": "Forge", "status": "review", "updated": "2026-11-06T18:55:01Z"}]})
        agents, runs, meta = ls.build(d, runs=[], t=T)
        self.assertEqual({a["id"] for a in agents}, {"b2:forge", "hq:vigil", "hq:claude"})
        self.assertEqual(meta["refreshed_at"], "2026-11-08T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
