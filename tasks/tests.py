from django.test import TestCase, Client
from .scoring import calculate_task_score, detect_cycles
from datetime import date, timedelta

class ScoringUnitTests(TestCase):
    def test_overdue_task(self):
        t = {"id": 1, "title": "old", "due_date": (date.today() - timedelta(days=2)).isoformat(), "importance": 5, "estimated_hours": 2}
        score, explanation, flags = calculate_task_score(t)
        self.assertTrue(score > 100)
        self.assertTrue(flags.get("overdue"))

    def test_quick_win_boost(self):
        t = {"id": 2, "title": "quick", "due_date": (date.today() + timedelta(days=10)).isoformat(), "importance": 4, "estimated_hours": 0.5}
        score, explanation, flags = calculate_task_score(t, strategy="fastest_wins")
        self.assertIn("quick win", explanation)

    def test_dependency_cycle_detection(self):
        tasks = [
            {"id": "a", "dependencies": ["b"]},
            {"id": "b", "dependencies": ["c"]},
            {"id": "c", "dependencies": ["a"]},
        ]
        has_cycle, cycles = detect_cycles(tasks)
        self.assertTrue(has_cycle)
        self.assertTrue(len(cycles) >= 1)

class ViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_analyze_endpoint(self):
        tasks = [
            {"id": "1", "title": "T1", "due_date": (date.today() + timedelta(days=1)).isoformat(), "importance": 8, "estimated_hours": 2},
            {"id": "2", "title": "T2", "due_date": (date.today() + timedelta(days=5)).isoformat(), "importance": 6, "estimated_hours": 1},
        ]
        resp = self.client.post("/api/tasks/analyze/?strategy=smart_balance", data=tasks, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("tasks", data)
        self.assertTrue(isinstance(data["tasks"], list))
