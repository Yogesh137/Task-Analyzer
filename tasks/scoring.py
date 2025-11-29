from datetime import date, datetime, timedelta
from collections import defaultdict, deque

DATE_FORMATS = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]

def parse_date(d):
    if not d:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(d, fmt).date()
        except Exception:
            pass
    try:
        # try fromisoformat
        return datetime.fromisoformat(d).date()
    except Exception:
        return None

def detect_cycles(tasks):
    """
    tasks: list of dicts with 'id' and 'dependencies'
    returns: (has_cycle: bool, cycles: list of lists)
    Implement DFS-based cycle detection.
    """
    graph = defaultdict(list)
    ids = set()
    for t in tasks:
        tid = t.get('id')
        ids.add(tid)
    for t in tasks:
        a = t.get('id')
        for b in (t.get('dependencies') or []):
            # only add edges if dependency id exists in list
            if b in ids:
                graph[a].append(b)

    visited = {}
    cycles = []

    def dfs(node, stack):
        if node not in visited:
            visited[node] = 1  # visiting
            stack.append(node)
            for nb in graph.get(node, []):
                if visited.get(nb) == 1:
                    # cycle found: nodes from nb to end of stack
                    idx = stack.index(nb) if nb in stack else 0
                    cycles.append(stack[idx:] + [nb])
                elif visited.get(nb) is None:
                    dfs(nb, stack)
            stack.pop()
            visited[node] = 2  # visited

    for node in list(ids):
        if visited.get(node) is None:
            dfs(node, [])

    return (len(cycles) > 0, cycles)

def base_score_components(task, today=None):
    """
    Returns (score, reasons_dict)
    Reasons dict contains explanation parts.
    """
    if today is None:
        today = date.today()

    score = 0.0
    reasons = []

    importance = int(task.get('importance') or 5)
    est_hours = float(task.get('estimated_hours') or 1)
    deps = task.get('dependencies') or []
    due_date = parse_date(task.get('due_date'))

    # Urgency
    if due_date:
        days_until = (due_date - today).days
        if days_until < 0:
            # overdue
            score += 200
            reasons.append("overdue")
        elif days_until <= 1:
            score += 80
            reasons.append("due ≤ 1 day")
        elif days_until <= 3:
            score += 50
            reasons.append("due ≤ 3 days")
        else:
            urgency_value = max(0, 20 - 0.5 * days_until)
            score += urgency_value
            if urgency_value > 0:
                reasons.append(f"due in {days_until} days")
    else:
        reasons.append("no due date")

    # Importance
    score += importance * 8
    reasons.append(f"importance {importance}")

    # Effort (quick wins)
    if est_hours <= 1:
        score += 20
        reasons.append("quick win")
    elif est_hours <= 3:
        score += 10
        reasons.append("small task")
    else:
        # mild negative for large estimates
        penalty = max(0, 0.5 * (est_hours - 3))
        score -= penalty
        if penalty > 0:
            reasons.append(f"big task ({est_hours}h)")

    # Dependency penalty applied later with context
    return score, reasons

def calculate_task_score(task, tasks_by_id=None, strategy="smart_balance", today=None):
    """
    Calculate final score depending on strategy.
    strategy: one of 'smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'
    tasks_by_id: optional mapping id -> task to check unresolved dependencies/completions
    Returns: (score: float, explanation: str, flags: dict)
    """
    if today is None:
        today = date.today()

    score, reasons = base_score_components(task, today=today)

    # Strategy adjustments
    importance = int(task.get('importance') or 5)
    est_hours = float(task.get('estimated_hours') or 1)
    due_date = parse_date(task.get('due_date'))

    # Strategy-specific multipliers / overrides
    if strategy == "fastest_wins":
        # boost small tasks heavily
        if est_hours <= 1:
            score += 40
            reasons.append("strategy: fastest_wins quick boost")
        elif est_hours <= 3:
            score += 10
    elif strategy == "high_impact":
        # boost importance
        score += importance * 10
        reasons.append("strategy: high_impact")
    elif strategy == "deadline_driven":
        # heavy urgency emphasis
        if due_date:
            days_until = (due_date - today).days
            if days_until < 0:
                score += 300
            else:
                score += max(0, 100 - 2 * days_until)
        reasons.append("strategy: deadline_driven")
    else:
        # smart_balance: mild default behavior already applied
        reasons.append("strategy: smart_balance")

    # Dependencies: penalize unresolved dependencies unless they are completed
    unresolved = 0
    blocking_count = 0
    if task.get('dependencies'):
        deps = task.get('dependencies') or []
        if tasks_by_id:
            for d in deps:
                dep_task = tasks_by_id.get(d)
                if dep_task:
                    if not dep_task.get('completed', False):
                        unresolved += 1
                else:
                    unresolved += 1  # unknown dependency -> assume unresolved
        else:
            unresolved = len(deps)

    if unresolved > 0:
        dep_penalty = unresolved * 30
        score -= dep_penalty
        reasons.append(f"{unresolved} unresolved dependency(ies)")

    # Safety: clamp floor
    score = max(score, -1000)
    explanation = "; ".join(reasons)
    flags = {
        "overdue": (due_date is not None and (due_date - today).days < 0),
        "has_dependencies": len(task.get('dependencies') or []) > 0
    }
    return round(score, 2), explanation, flags
