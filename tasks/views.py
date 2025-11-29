import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .scoring import calculate_task_score, detect_cycles
from datetime import date

VALID_STRATEGIES = {"smart_balance", "fastest_wins", "high_impact", "deadline_driven"}

def validate_tasks_input(payload):
    if isinstance(payload, list):
        tasks = payload
    elif isinstance(payload, dict) and "tasks" in payload:
        tasks = payload["tasks"]
    else:
        raise ValueError("Payload must be a list of tasks or an object with 'tasks' key.")
    # basic normalization: ensure each task has id
    for idx, t in enumerate(tasks):
        if t.get("id") is None:
            t["id"] = f"tmp_{idx}"
    return tasks

@csrf_exempt
def analyze_tasks(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed.")
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload.")
    try:
        tasks = validate_tasks_input(payload)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    strategy = request.GET.get("strategy", "smart_balance")
    if strategy not in VALID_STRATEGIES:
        strategy = "smart_balance"

    # build id mapping
    tasks_by_id = {t.get("id"): t for t in tasks}

    # detect cycles
    has_cycle, cycles = detect_cycles(tasks)

    results = []
    for t in tasks:
        score, explanation, flags = calculate_task_score(t, tasks_by_id=tasks_by_id, strategy=strategy, today=date.today())
        tout = t.copy()
        tout["score"] = score
        tout["explanation"] = explanation
        tout["flags"] = flags
        results.append(tout)

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    response = {"tasks": results_sorted, "strategy": strategy, "dependency_cycles": cycles}
    return JsonResponse(response, safe=False)

@csrf_exempt
def suggest_tasks(request):
    """
    GET: optional - returns sample instructions
    POST: accept tasks list (same as analyze), returns top 3 with plain explanations
    """
    if request.method == "GET":
        return JsonResponse({"info": "POST a list of tasks (JSON array) to get top-3 suggestions. Use query param ?strategy=... to choose strategy."})
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload.")
    try:
        tasks = validate_tasks_input(payload)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    strategy = request.GET.get("strategy", "smart_balance")
    if strategy not in VALID_STRATEGIES:
        strategy = "smart_balance"

    tasks_by_id = {t.get("id"): t for t in tasks}
    scored = []
    for t in tasks:
        s, exp, flags = calculate_task_score(t, tasks_by_id=tasks_by_id, strategy=strategy)
        scored.append({"task": t, "score": s, "explanation": exp, "flags": flags})

    top3 = sorted(scored, key=lambda x: x["score"], reverse=True)[:3]
    suggestions = []
    for item in top3:
        suggestions.append({
            "id": item["task"].get("id"),
            "title": item["task"].get("title"),
            "score": item["score"],
            "why": item["explanation"],
            "flags": item["flags"]
        })
    return JsonResponse({"strategy": strategy, "top_3": suggestions})
