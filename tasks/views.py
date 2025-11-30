# tasks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .scoring import analyze_tasks
from .validators import (
    validate_task,
    validate_strategy,
    TaskValidationError,
)

def serialize_task(t):
    """Convert ScoredTask dataclass into JSON-friendly dict."""
    return {
        "id": t.id,
        "title": t.title,
        "final_score": t.final_score,
        "urgency_score": t.urgency_score,
        "effort_score": t.effort_score,
        "dependency_score": t.dependency_score,
        "strategy": t.strategy,
        "circular_dependency": t.circular_dependency,
        "explanations": t.explanations,
    }


def _parse_and_validate_request(request):
    """
    Common helper used by both /analyze and /suggest.

    Returns:
        (pending_tasks, strategy, error_response)

    If error_response is not None, the caller should immediately return it.
    """
    data = request.data

    if not isinstance(data, dict):
        return None, None, Response(
            {"error": "Request body must be a JSON object."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tasks = data.get("tasks")
    strategy = data.get("strategy", "smart_balance")

    if tasks is None:
        return None, None, Response(
            {"error": "'tasks' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(tasks, list) or len(tasks) == 0:
        return None, None, Response(
            {"error": "'tasks' must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_strategy(strategy)
    except TaskValidationError as e:
        return None, None, Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    all_ids = set()
    for raw_task in tasks:
        if isinstance(raw_task, dict) and "id" in raw_task:
            all_ids.add(str(raw_task["id"]))

    try:
        for raw_task in tasks:
            validate_task(raw_task, all_ids=all_ids)
    except TaskValidationError as e:
        return None, None, Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    pending = [t for t in tasks if not t.get("completed", False)]

    return pending, strategy, None


class TaskAnalysisView(APIView):
    """
    POST /api/tasks/analyze/

    Body:
    {
      "strategy": "smart_balance",
      "tasks": [ ... ]
    }
    """

    def post(self, request):
        pending, strategy, error_response = _parse_and_validate_request(request)
        if error_response is not None:
            return error_response

        if not pending:
            return Response([], status=status.HTTP_200_OK)

        try:
            result = analyze_tasks(pending, strategy)
        except Exception as e:
            return Response(
                {"error": f"Failed to analyze tasks: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            [serialize_task(t) for t in result],
            status=status.HTTP_200_OK,
        )


class TaskSuggestionView(APIView):
    """
    POST /api/tasks/suggest/

    Body:
    {
      "strategy": "smart_balance",
      "tasks": [ ... ]
    }

    Response (current version = single best task):
    {
      "recommended_task": { ... }  or  null
    }
    """

    def post(self, request):
        pending, strategy, error_response = _parse_and_validate_request(request)
        if error_response is not None:
            return error_response

        if not pending:
            return Response(
                {"recommended_task": None},
                status=status.HTTP_200_OK,
            )

        try:
            result = analyze_tasks(pending, strategy)
        except Exception as e:
            return Response(
                {"error": f"Failed to compute suggestion: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not result:
            return Response(
                {"recommended_task": None},
                status=status.HTTP_200_OK,
            )

        best = result[0]
        return Response(
            {"recommended_task": serialize_task(best)},
            status=status.HTTP_200_OK,
        )
