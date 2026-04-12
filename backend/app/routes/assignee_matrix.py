from collections import Counter, defaultdict
from datetime import datetime

from flask import Blueprint, current_app, jsonify
import requests

from app.routes.tickets import (
    _jira_auth,
    _jira_config_errors,
    _jql_for_category,
    _normalize_jira_base_url,
    _normalize_jira_value,
)

assignee_matrix_bp = Blueprint("assignee_matrix", __name__)


def _jira_date(value):
    if not value:
        return "No date"
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return value[:10]
    return parsed.strftime("%Y-%m-%d")


def _fetch_jira_issues(category, fields):
    base_url = _normalize_jira_base_url(current_app.config["JIRA_BASE_URL"])
    search_jql_url = f"{base_url}/rest/api/3/search/jql"
    issues = []
    total = 0
    next_page_token = None

    while True:
        request_body = {
            "jql": _jql_for_category(category),
            "maxResults": 100,
            "fields": fields,
        }
        if next_page_token:
            request_body["nextPageToken"] = next_page_token

        response = requests.post(
            search_jql_url,
            json=request_body,
            auth=_jira_auth(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        if response.status_code >= 400:
            details = response.text[:300]
            return {
                "ok": False,
                "status": response.status_code,
                "message": f"Jira API error ({response.status_code}): {details}",
                "issues": [],
                "total": 0,
            }

        payload = response.json()
        issues.extend(payload.get("issues", []))
        total = payload.get("total", len(issues))
        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return {
        "ok": True,
        "status": 200,
        "message": "Assignee matrix fetched successfully",
        "issues": issues,
        "total": total,
    }


def _person_name(value):
    return _normalize_jira_value(value) or "Unassigned"


@assignee_matrix_bp.route("/", methods=["GET"])
def get_assignee_matrix():
    missing = _jira_config_errors()
    if missing:
        return (
            jsonify(
                {
                    "data": {},
                    "message": f"Missing Jira configuration: {', '.join(missing)}",
                }
            ),
            400,
        )

    l0_field_id = current_app.config.get("JIRA_L0_ASSIGNEE_FIELD_ID")
    tes_supervision_field_id = current_app.config.get("JIRA_TES_SUPERVISION_FIELD_ID")
    fields = [
        "summary",
        "status",
        "assignee",
        "resolutiondate",
        l0_field_id,
        tes_supervision_field_id,
    ]

    try:
        active_result = _fetch_jira_issues("active", fields)
        if not active_result["ok"]:
            return (
                jsonify({"data": {}, "message": active_result["message"]}),
                active_result["status"],
            )

        resolved_result = _fetch_jira_issues("resolved", fields)
        if not resolved_result["ok"]:
            return (
                jsonify({"data": {}, "message": resolved_result["message"]}),
                resolved_result["status"],
            )
    except requests.exceptions.RequestException as exc:
        return jsonify({"data": {}, "message": f"Unable to reach Jira: {exc}"}), 502

    active_counts = defaultdict(Counter)
    resolved_counts = defaultdict(Counter)
    role_totals = Counter()
    resolved_by_date = Counter()
    resolved_by_assignee_date = defaultdict(Counter)

    role_fields = (
        ("Assignee", "assignee"),
        ("L0 Assignee", l0_field_id),
        ("TES Supervision", tes_supervision_field_id),
    )

    for issue in active_result["issues"]:
        fields_data = issue.get("fields", {})
        for role, field_id in role_fields:
            person = _person_name(fields_data.get(field_id))
            active_counts[(role, person)]["active_tickets"] += 1
            if person != "Unassigned":
                role_totals[role] += 1

    for issue in resolved_result["issues"]:
        fields_data = issue.get("fields", {})
        resolution_date = _jira_date(fields_data.get("resolutiondate"))
        resolved_by_date[resolution_date] += 1
        assignee = _person_name(fields_data.get("assignee"))
        resolved_by_assignee_date[assignee][resolution_date] += 1

        for role, field_id in role_fields:
            person = _person_name(fields_data.get(field_id))
            resolved_counts[(role, person)]["resolved_tickets"] += 1

    matrix_keys = set(active_counts.keys()) | set(resolved_counts.keys())
    matrix_rows = []
    for role, person in matrix_keys:
        active_count = active_counts[(role, person)]["active_tickets"]
        resolved_count = resolved_counts[(role, person)]["resolved_tickets"]
        matrix_rows.append(
            {
                "role": role,
                "person": person,
                "active_tickets": active_count,
                "resolved_tickets": resolved_count,
                "total_tickets": active_count + resolved_count,
            }
        )

    resolved_dates = sorted(resolved_by_date)
    top_resolved_assignees = [
        assignee
        for assignee, _ in Counter(
            {
                assignee: sum(counts.values())
                for assignee, counts in resolved_by_assignee_date.items()
            }
        ).most_common(5)
    ]

    return jsonify(
        {
            "data": {
                "active_total": active_result["total"],
                "resolved_total": resolved_result["total"],
                "role_totals": [
                    {"role": role, "count": role_totals[role]}
                    for role in ("Assignee", "L0 Assignee", "TES Supervision")
                ],
                "matrix": sorted(
                    matrix_rows,
                    key=lambda item: (
                        item["role"],
                        -item["active_tickets"],
                        -item["resolved_tickets"],
                        item["person"],
                    ),
                ),
                "resolved_by_date": [
                    {"date": date, "count": resolved_by_date[date]}
                    for date in resolved_dates
                ],
                "resolved_assignee_trends": [
                    {
                        "person": assignee,
                        "points": [
                            {
                                "date": date,
                                "count": resolved_by_assignee_date[assignee][date],
                            }
                            for date in resolved_dates
                        ],
                    }
                    for assignee in top_resolved_assignees
                ],
            },
            "message": "Assignee matrix fetched successfully",
        }
    )
