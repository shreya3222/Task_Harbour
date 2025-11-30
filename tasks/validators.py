# tasks/validators.py
from datetime import datetime


class TaskValidationError(Exception):
    """Raised when a single task object is invalid."""
    pass


ALLOWED_STRATEGIES = {"fastest_wins", "high_impact", "deadline_driven", "smart_balance"}


def validate_strategy(strategy: str):
    if strategy not in ALLOWED_STRATEGIES:
        raise TaskValidationError(
            f"Invalid strategy '{strategy}'. "
            f"Allowed values: {', '.join(sorted(ALLOWED_STRATEGIES))}."
        )


def validate_task(task: dict, all_ids=None):
    """
    Validate a single task dict.

    Expected shape on backend (after frontend formatting):
    {
      "id": "T1",
      "title": "Some task",
      "importance": 1-10 (int),
      "estimated_hours": number >= 1,
      "due_date": "YYYY-MM-DD",
      "dependencies": ["T1", "T2"],
      "completed": bool,
      ... other fields ignored
    }
    """
    if not isinstance(task, dict):
        raise TaskValidationError("Each task must be a JSON object.")

    required = ["id", "title", "importance", "estimated_hours", "due_date", "dependencies", "completed"]
    for field in required:
        if field not in task:
            raise TaskValidationError(f"Task is missing required field '{field}'.")

    task_id = str(task.get("id"))

    title = str(task.get("title", "")).strip()
    if not title:
        raise TaskValidationError(f"Task {task_id}: title cannot be empty.")

    try:
        importance = int(task.get("importance"))
    except (TypeError, ValueError):
        raise TaskValidationError(f"Task {task_id}: importance must be a number between 1 and 10.")
    if importance < 1 or importance > 10:
        raise TaskValidationError(f"Task {task_id}: importance must be between 1 and 10.")

    try:
        hours = float(task.get("estimated_hours"))
    except (TypeError, ValueError):
        raise TaskValidationError(f"Task {task_id}: estimated_hours must be a positive number.")
    if hours < 1:
        raise TaskValidationError(f"Task {task_id}: estimated_hours must be at least 1 hour.")

    due_date = str(task.get("due_date", "")).strip()
    if not due_date:
        raise TaskValidationError(f"Task {task_id}: due_date is required.")
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        raise TaskValidationError(
            f"Task {task_id}: due_date must be a valid date in 'YYYY-MM-DD' format."
        )

    deps = task.get("dependencies", [])
    if not isinstance(deps, list):
        raise TaskValidationError(f"Task {task_id}: dependencies must be a list of task ids (e.g. ['T1','T2']).")

    if all_ids is not None:
        for dep in deps:
            if dep not in all_ids:
                raise TaskValidationError(
                    f"Task {task_id}: dependency '{dep}' does not exist in the submitted tasks."
                )

    if not isinstance(task.get("completed"), bool):
        raise TaskValidationError(f"Task {task_id}: 'completed' must be true or false.")
