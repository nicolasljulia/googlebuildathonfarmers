from app.data_sources.disease_library import DISEASE_LIBRARY


def _eval_condition(cond, obs):
    field   = cond.get("field")
    op      = cond.get("op")
    value   = cond.get("value")
    obs_val = obs.get(field)
    if obs_val is None:
        return False
    try:
        if op == ">=":      return float(obs_val) >= float(value)
        if op == "<=":      return float(obs_val) <= float(value)
        if op == ">":       return float(obs_val) > float(value)
        if op == "<":       return float(obs_val) < float(value)
        if op == "==":      return str(obs_val) == str(value)
        if op == "in":      return obs_val in value
        if op == "between": return float(value[0]) <= float(obs_val) <= float(value[1])
        if op == "contains":return str(value).lower() in str(obs_val).lower()
    except (TypeError, ValueError):
        return False
    return False


def _eval_rule(row, obs):
    logic = row.get("rule_logic")
    if not logic:
        return False
    logic_type = logic.get("logic", "AND")
    if logic_type in ("EXTERNAL", "CROP_SPECIFIC"):
        return False
    conditions = logic.get("conditions", [])
    if not conditions:
        return False
    results = [_eval_condition(c, obs) for c in conditions]
    if logic_type == "AND":
        return all(results)
    if logic_type == "OR":
        return any(results)
    return False


def run_rules_engine(obs):
    severity_order = {"Severe": 0, "High": 1, "Medium": 2, "Low": 3}
    triggered = []
    seen_ids  = set()

    for row in DISEASE_LIBRARY:
        if row.get("category") == "Perfect Conditions":
            continue
        crop_col = row.get("crop", "Generic")
        if crop_col != "Generic" and crop_col.lower() != obs.get("crop_type", "").lower():
            continue
        if not _eval_rule(row, obs):
            continue
        issue_id = row.get("issue_id", "")
        if issue_id in seen_ids:
            continue
        seen_ids.add(issue_id)
        triggered.append({
            "issue_id":       issue_id,
            "name":           row.get("issue_name", ""),
            "category":       row.get("category", ""),
            "level":          row.get("severity", "Medium"),
            "detail":         row.get("notes", ""),
            "causal_agent":   row.get("causal_agent", ""),
            "recommendation": row.get("recommendation", ""),
            "urgency":        row.get("urgency", ""),
        })

    triggered.sort(key=lambda x: severity_order.get(x["level"], 99))
    return triggered
