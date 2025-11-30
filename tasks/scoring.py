from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple

@dataclass
class ScoredTask:
    id: str
    title: str
    due_date: Optional[date]
    estimated_hours: Optional[float]
    importance: int
    dependencies: List[str]

    urgency_score: float
    effort_score: float
    dependency_score: float  
    final_score: float

    strategy: str
    circular_dependency: bool = False
    explanations: List[str] = field(default_factory=list)

def _parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None


def _compute_urgency(due: Optional[date], today: Optional[date] = None) -> Tuple[float, List[str]]:
    if today is None:
        today = date.today()

    if due is None:
        return 2.0, ["No due date provided; low urgency."]
    days = (due - today).days
    if days < 0:
        return 10.0, ["Task is overdue."]
    if days <= 1:
        return 9.0, ["Due very soon."]
    if days <= 3:
        return 8.0, ["Due in next few days."]
    if days <= 7:
        return 6.0, ["Due within a week."]
    if days <= 14:
        return 4.0, ["Due within two weeks."]
    return 2.0, ["Due after two weeks."]


def _compute_effort(hours: Optional[float]) -> Tuple[float, List[str]]:
    if hours is None:
        return 4.0, ["Missing estimated hours."]
    if hours <= 1:
        return 10.0, ["Very small task."]
    if hours <= 2:
        return 8.0, ["Small task."]
    if hours <= 4:
        return 6.0, ["Medium task."]
    if hours <= 8:
        return 4.0, ["Large task."]
    return 2.0, ["Very large task."]

def _compute_dependency_scores(tasks: List[Dict]) -> Dict[str, Tuple[float, List[str]]]:
    dependents = {str(t["id"]): 0 for t in tasks}

    for t in tasks:
        for dep in t.get("dependencies", []):
            dep = str(dep)
            if dep in dependents:
                dependents[dep] += 1

    results = {}
    for tid, cnt in dependents.items():
        if cnt == 0:
            results[tid] = (0.0, ["No tasks are blocked by this task."])
        elif cnt == 1:
            results[tid] = (5.0, ["This task blocks 1 other task."])
        elif 2 <= cnt <= 4:
            results[tid] = (8.0, [f"This task blocks {cnt} tasks."])
        else:
            results[tid] = (10.0, [f"This task blocks many tasks ({cnt})."])
    return results

def _detect_cycles(tasks: List[Dict]) -> Dict[str, bool]:
    graph = {str(t["id"]): [str(d) for d in t.get("dependencies", [])] for t in tasks}
    visited, visiting = set(), set()
    in_cycle = {tid: False for tid in graph}

    def dfs(node, stack):
        if node in visiting:
            loop_start = stack.index(node)
            for n in stack[loop_start:]:
                in_cycle[n] = True
            return

        if node in visited:
            return

        visiting.add(node)
        stack.append(node)

        for nxt in graph.get(node, []):
            dfs(nxt, stack)

        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for n in graph:
        if n not in visited:
            dfs(n, [])

    return in_cycle

def _weights(strategy: str) -> Dict[str, float]:
    strategy = strategy.lower()

    if strategy == "fastest_wins":
        return {"urgency": 0.2, "importance": 0.2, "effort": 0.5, "dependency": 0.1}

    if strategy == "high_impact":
        return {"urgency": 0.2, "importance": 0.6, "effort": 0.1, "dependency": 0.1}

    if strategy == "deadline_driven":
        return {"urgency": 0.6, "importance": 0.2, "effort": 0.1, "dependency": 0.1}

    return {"urgency": 0.3, "importance": 0.4, "effort": 0.15, "dependency": 0.15}

def analyze_tasks(tasks: List[Dict], strategy: str = "smart_balance") -> List[ScoredTask]:
    dep_scores = _compute_dependency_scores(tasks)
    cycles = _detect_cycles(tasks)
    w = _weights(strategy)

    scored = []

    for t in tasks:
        tid = str(t["id"])
        dependencies = [str(d) for d in t.get("dependencies", [])]

        title = t.get("title", "(untitled)")
        due = _parse_date(t.get("due_date"))
        hours = float(t["estimated_hours"]) if t.get("estimated_hours") is not None else None
        importance = max(1, min(10, int(t.get("importance", 5))))

        urgency, exp_u = _compute_urgency(due)
        effort, exp_e = _compute_effort(hours)
        dep_score, exp_d = dep_scores.get(tid, (0.0, ["No dependency info"]))

        dep_count = len(dependencies)
        if dep_count == 0:
            dep_penalty, exp_p = 0, ["No prerequisites. Can start immediately."]
        elif dep_count == 1:
            dep_penalty, exp_p = -1, ["Has 1 prerequisite task."]
        elif dep_count == 2:
            dep_penalty, exp_p = -3, ["Has 2 prerequisite tasks."]
        else:
            dep_penalty, exp_p = -5, [f"Has {dep_count} prerequisite tasks."]

        explanations = exp_u + exp_e + exp_d + exp_p
        explanations.append(f"Importance: {importance}/10")

        base = (
            w["urgency"] * urgency +
            w["importance"] * importance +
            w["effort"] * effort +
            w["dependency"] * dep_score +
            dep_penalty
        )

        circular = cycles.get(tid, False)
        final_score = base * (0.7 if circular else 1)

        if circular:
            explanations.append("Circular dependency detected. Score reduced.")

        scored.append(
            ScoredTask(
                id=tid,
                title=title,
                due_date=due,
                estimated_hours=hours,
                importance=importance,
                dependencies=dependencies,
                urgency_score=urgency,
                effort_score=effort,
                dependency_score=dep_score,
                final_score=round(final_score, 2),
                strategy=strategy,
                circular_dependency=circular,
                explanations=explanations,
            )
        )

    scored.sort(key=lambda x: (-x.final_score, -x.urgency_score))
    return scored
