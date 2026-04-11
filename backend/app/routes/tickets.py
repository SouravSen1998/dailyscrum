from flask import Blueprint, current_app, jsonify
import requests


tickets_bp = Blueprint("tickets", __name__)


def _normalize_jira_base_url(raw_base_url):
    if not raw_base_url:
        return raw_base_url

    normalized = raw_base_url.rstrip("/")
    suffixes_to_trim = (
        "/rest/api/3/search/jql",
        "/rest/api/3/search",
        "/rest/api/2/search",
        "/rest/api/3",
        "/rest/api/2",
        "/rest/api",
    )

    for suffix in suffixes_to_trim:
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]

    return normalized


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

    base_url = _normalize_jira_base_url(current_app.config["JIRA_BASE_URL"])
    jql = current_app.config.get("JIRA_JQL") or "ORDER BY updated DESC"
    search_jql_url = f"{base_url}/rest/api/3/search/jql"
    client_name_field_id = current_app.config.get("JIRA_CLIENT_NAME_FIELD_ID")
    l0_assignee_field_id = current_app.config.get("JIRA_L0_ASSIGNEE_FIELD_ID")
    pcmc_inclusion_date_field_id = current_app.config.get(
        "JIRA_PCMC_INCLUSION_DATE_FIELD_ID"
    )
    auth = (
        current_app.config["JIRA_EMAIL"],
        current_app.config["JIRA_API_TOKEN"],
    )

    try:
        request_body = {
            "jql": jql,
            "maxResults": 50,
            "fields": [
                "summary",
                "status",
                "priority",
                client_name_field_id,
                l0_assignee_field_id,
                pcmc_inclusion_date_field_id,
            ],
            "expand": "names",
        }

        response = requests.post(
            search_jql_url,
            json=request_body,
            auth=auth,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
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
    field_names = payload.get("names", {})

    def field_id_for(label):
        label_lower = label.strip().lower()
        for field_id, name in field_names.items():
            if (name or "").strip().lower() == label_lower:
                return field_id
        return None

    def normalize_value(value):
        if value is None:
            return None
        if isinstance(value, dict):
            for key in ("displayName", "name", "value"):
                if value.get(key):
                    return value.get(key)
            return str(value)
        if isinstance(value, list):
            normalized_values = [normalize_value(item) for item in value]
            return ", ".join([item for item in normalized_values if item]) or None
        return value

    client_name_field_id = client_name_field_id or field_id_for("Client Name")
    l0_assignee_field_id = l0_assignee_field_id or field_id_for("L0 TES Assignee")
    pcmc_inclusion_date_field_id = (
        pcmc_inclusion_date_field_id or field_id_for("PCMC Inclusion Date")
    )

    normalized = []
    for issue in issues:
        fields = issue.get("fields", {})
        priority = fields.get("priority") or {}
        status = fields.get("status") or {}
        pcmc_inclusion_date = normalize_value(fields.get(pcmc_inclusion_date_field_id))

        normalized.append(
            {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": status.get("name"),
                "client_name": normalize_value(fields.get(client_name_field_id)),
                "priority": priority.get("name"),
                "l0_assignee": normalize_value(fields.get(l0_assignee_field_id)),
                "pcmc_inclusion_date": pcmc_inclusion_date,
                "is_pcmc_ticket": bool(pcmc_inclusion_date),
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
