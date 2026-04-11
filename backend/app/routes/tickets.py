from flask import Blueprint, current_app, jsonify
import requests


tickets_bp = Blueprint("tickets", __name__)


def _jira_config_errors():
    missing = []
    if not current_app.config.get("JIRA_BASE_URL"):
        missing.append("JIRA_BASE_URL")
    if not current_app.config.get("JIRA_EMAIL"):
        missing.append("JIRA_EMAIL")
    if not current_app.config.get("JIRA_API_TOKEN"):
        missing.append("JIRA_API_TOKEN")
    return missing


def _jira_search():
    missing = _jira_config_errors()
    if missing:
        return {
            "ok": False,
            "status": 400,
            "message": f"Missing Jira configuration: {', '.join(missing)}",
            "data": [],
        }

    base_url = current_app.config["JIRA_BASE_URL"].rstrip("/")
    jql = current_app.config.get("JIRA_JQL") or "ORDER BY updated DESC"
    search_url = f"{base_url}/rest/api/3/search/jql"
    auth = (
        current_app.config["JIRA_EMAIL"],
        current_app.config["JIRA_API_TOKEN"],
    )

    try:
        response = requests.post(
            search_url,
            json={
                "jql": jql,
                "maxResults": 50,
                "fields": ["summary", "status", "priority", "assignee", "updated"],
            },
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "status": 502,
            "message": f"Unable to reach Jira: {exc}",
            "data": [],
        }

    if response.status_code >= 400:
        details = response.text[:300]
        return {
            "ok": False,
            "status": response.status_code,
            "message": f"Jira API error ({response.status_code}): {details}",
            "data": [],
        }

    payload = response.json()
    issues = payload.get("issues", [])
    normalized = []
    for issue in issues:
        fields = issue.get("fields", {})
        assignee = fields.get("assignee") or {}
        priority = fields.get("priority") or {}
        status = fields.get("status") or {}

        normalized.append(
            {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": status.get("name"),
                "priority": priority.get("name"),
                "assignee": assignee.get("displayName"),
                "updated": fields.get("updated"),
            }
        )

    return {
        "ok": True,
        "status": 200,
        "message": "Jira tickets fetched successfully",
        "data": normalized,
        "total": payload.get("total", len(normalized)),
    }


@tickets_bp.route("/", methods=["GET"])
def get_tickets():
    result = _jira_search()
    return (
        jsonify(
            {
                "data": result["data"],
                "total": result.get("total", len(result["data"])),
                "message": result["message"],
            }
        ),
        result["status"],
    )


@tickets_bp.route("/sync", methods=["POST"])
def sync_tickets():
    result = _jira_search()
    return (
        jsonify(
            {
                "synced": result["status"] == 200,
                "count": len(result["data"]),
                "message": result["message"],
                "data": result["data"],
            }
        ),
        result["status"],
    )
