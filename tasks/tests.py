from django.test import TestCase
from datetime import date, timedelta
import json

from .scoring import (
    analyze_tasks,
    _compute_urgency,
    _compute_effort,
    _compute_dependency_scores,
    _detect_cycles,
)


class ScoringUnitTests(TestCase):
    """Tests for scoring algorithm (urgency, effort, deps, cycles)."""

    def test_urgency_scoring(self):
        today = date.today()

        score, _ = _compute_urgency(today + timedelta(days=1), today)
        self.assertEqual(score, 9.0)

        score, _ = _compute_urgency(today + timedelta(days=3), today)
        self.assertEqual(score, 8.0)

        score, _ = _compute_urgency(today + timedelta(days=7), today)
        self.assertEqual(score, 6.0)

        score, _ = _compute_urgency(today + timedelta(days=20), today)
        self.assertEqual(score, 2.0)

    def test_effort_scoring(self):
        self.assertEqual(_compute_effort(1)[0], 10.0)
        self.assertEqual(_compute_effort(2)[0], 8.0)
        self.assertEqual(_compute_effort(4)[0], 6.0)
        self.assertEqual(_compute_effort(8)[0], 4.0)
        self.assertEqual(_compute_effort(20)[0], 2.0)

    def test_dependency_scores(self):
        tasks = [
            {"id": "T1", "dependencies": []},
            {"id": "T2", "dependencies": ["T1"]},
            {"id": "T3", "dependencies": ["T1"]},
        ]
        dep_scores = _compute_dependency_scores(tasks)

        self.assertEqual(dep_scores["T1"][0], 8.0)
        self.assertEqual(dep_scores["T2"][0], 0.0)
        self.assertEqual(dep_scores["T3"][0], 0.0)

    def test_prerequisite_penalty(self):
        tasks = [
            {"id": "A", "title": "A", "due_date": None, "estimated_hours": 2, "importance": 5, "dependencies": []},
            {"id": "B", "title": "B", "due_date": None, "estimated_hours": 2, "importance": 5, "dependencies": ["A"]},
            {"id": "C", "title": "C", "due_date": None, "estimated_hours": 2, "importance": 5, "dependencies": ["A", "B"]},
        ]
        results = analyze_tasks(tasks)

        scores = {t.id: t.final_score for t in results}

        self.assertGreater(scores["A"], scores["B"])
        self.assertGreater(scores["B"], scores["C"])

    def test_cycle_detection(self):
        tasks = [
            {"id": "X", "dependencies": ["Y"]},
            {"id": "Y", "dependencies": ["X"]},
        ]
        cycles = _detect_cycles(tasks)
        self.assertTrue(cycles["X"])
        self.assertTrue(cycles["Y"])


class StrategyTests(TestCase):
    """Tests each strategy affects scoring differently."""

    def make_tasks(self):
        return [
            {
                "id": "T1",
                "title": "Resume",
                "due_date": (date.today() + timedelta(days=2)).isoformat(),
                "estimated_hours": 1,
                "importance": 9,
                "dependencies": []
            },
            {
                "id": "T2",
                "title": "Portfolio",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
                "estimated_hours": 6,
                "importance": 7,
                "dependencies": []
            },
        ]

    def test_smart_balance(self):
        result = analyze_tasks(self.make_tasks(), strategy="smart_balance")
        self.assertEqual(result[0].id, "T1")

    def test_deadline_driven(self):
        result = analyze_tasks(self.make_tasks(), strategy="deadline_driven")
        self.assertEqual(result[0].id, "T1")

    def test_high_impact(self):
        result = analyze_tasks(self.make_tasks(), strategy="high_impact")
        self.assertEqual(result[0].id, "T1")

    def test_fastest_wins_strategy(self):
        res = analyze_tasks(self.make_tasks(), strategy="fastest_wins")
        self.assertEqual(res[0].id, "T1")


class RankingTests(TestCase):
    """Tests if sorting logic works."""

    def test_sorting_order(self):
        tasks = [
            {"id": "A", "title": "A", "due_date": None, "estimated_hours": 10, "importance": 1, "dependencies": []},
            {"id": "B", "title": "B", "due_date": None, "estimated_hours": 1, "importance": 10, "dependencies": []},
        ]
        result = analyze_tasks(tasks)
        self.assertEqual(result[0].id, "B")

class APITests(TestCase):
    """Tests REST API endpoints using your actual URL structure."""

    def test_analyze_api(self):
        url = "/api/tasks/analyze/"
        payload = {
            "strategy": "smart_balance",
            "tasks": [
                {
                    "id": "T1",
                    "title": "Resume",
                    "due_date": (date.today() + timedelta(days=2)).isoformat(),
                    "estimated_hours": 1,
                    "importance": 9,
                    "dependencies": []
                }
            ]
        }

        res = self.client.post(url, payload, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)
        self.assertEqual(res.json()[0]["id"], "T1")

    def test_suggest_api(self):
        url = "/api/tasks/suggest/"
        payload = {
            "strategy": "smart_balance",
            "tasks": [
                {
                    "id": "T1",
                    "title": "Resume",
                    "due_date": (date.today() + timedelta(days=2)).isoformat(),
                    "estimated_hours": 1,
                    "importance": 9,
                    "dependencies": []
                }
            ]
        }

        res = self.client.post(url, payload, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("recommended_task", res.json())
        self.assertEqual(res.json()["recommended_task"]["id"], "T1")


