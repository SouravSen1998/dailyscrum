import re

from flask import Blueprint, current_app, jsonify, request
import requests

from app.extensions import db
from app.models import TicketNote


tickets_bp = Blueprint("tickets", __name__)

STATUS_CLAUSE_PATTERN = re.compile(r"\bstatus\s+NOT\s+IN\s*\([^)]*\)", re.IGNORECASE)
TICKET_CATEGORIES = {
    "active": None,
    "resolved": 'status IN (Resolved, Canceled, Closed, "Ticket Shelved")',
    "roadmap": 'status = "Roadmap Candidate"',
}


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


def _jql_for_category(category):
    base_jql = current_app.config.get("JIRA_JQL") or "ORDER BY updated DESC"
    status_clause = TICKET_CATEGORIES.get(category)
    if not status_clause:
        return base_jql

    if STATUS_CLAUSE_PATTERN.search(base_jql):
        return STATUS_CLAUSE_PATTERN.sub(status_clause, base_jql, count=1)

    order_by_match = re.search(r"\s+ORDER\s+BY\s+", base_jql, re.IGNORECASE)
    if order_by_match:
        filters = base_jql[: order_by_match.start()]
        order_by = base_jql[order_by_match.start() :]
        return f"{filters} AND {status_clause}{order_by}"

    return f"{base_jql} AND {status_clause}"


def _jira_auth():
    return (
        current_app.config["JIRA_EMAIL"],
        current_app.config["JIRA_API_TOKEN"],
    )


def _adf_to_text(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_to_text(item) for item in node)
    if not isinstance(node, dict):
        return str(node)

    text = node.get("text", "")
    content = _adf_to_text(node.get("content", []))
    node_type = node.get("type")
    if node_type in ("paragraph", "heading", "listItem"):
        return f"{content}\n"
    if node_type in ("bulletList", "orderedList"):
        return f"{content}\n"
    if node_type == "hardBreak":
        return "\n"
    return f"{text}{content}"


def _jira_search(category="active"):
    missing = _jira_config_errors()
    if missing:
        return {
            "ok": False,
            "status": 400,
            "message": f"Missing Jira configuration: {', '.join(missing)}",
            "data": [],
        }

    base_url = _normalize_jira_base_url(current_app.config["JIRA_BASE_URL"])
    jql = _jql_for_category(category)
    search_jql_url = f"{base_url}/rest/api/3/search/jql"
    client_name_field_id = current_app.config.get("JIRA_CLIENT_NAME_FIELD_ID")
    l0_assignee_field_id = current_app.config.get("JIRA_L0_ASSIGNEE_FIELD_ID")
    pcmc_inclusion_date_field_id = current_app.config.get(
        "JIRA_PCMC_INCLUSION_DATE_FIELD_ID"
    )
    auth = _jira_auth()

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
    issue_keys = [issue.get("key") for issue in issues if issue.get("key")]
    notes_by_ticket_key = {
        note.ticket_key: note.note
        for note in TicketNote.query.filter(TicketNote.ticket_key.in_(issue_keys)).all()
    }

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
        ticket_key = issue.get("key")

        normalized.append(
            {
                "key": ticket_key,
                "browse_url": f"{base_url}/browse/{ticket_key}" if ticket_key else None,
                "summary": fields.get("summary"),
                "status": status.get("name"),
                "client_name": normalize_value(fields.get(client_name_field_id)),
                "priority": priority.get("name"),
                "l0_assignee": normalize_value(fields.get(l0_assignee_field_id)),
                "pcmc_inclusion_date": pcmc_inclusion_date,
                "is_pcmc_ticket": bool(pcmc_inclusion_date),
                "scrum_note": notes_by_ticket_key.get(ticket_key, ""),
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
    category = request.args.get("category", "active").strip().lower()
    if category not in TICKET_CATEGORIES:
        return (
            jsonify(
                {
                    "data": [],
                    "total": 0,
                    "message": f"Unsupported ticket category: {category}",
                }
            ),
            400,
        )

    result = _jira_search(category)
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
    category = request.args.get("category", "active").strip().lower()
    if category not in TICKET_CATEGORIES:
        return (
            jsonify(
                {
                    "synced": False,
                    "count": 0,
                    "message": f"Unsupported ticket category: {category}",
                    "data": [],
                }
            ),
            400,
        )

    result = _jira_search(category)
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


@tickets_bp.route("/<ticket_key>/comments", methods=["GET"])
def get_ticket_comments(ticket_key):
    missing = _jira_config_errors()
    if missing:
        return (
            jsonify(
                {
                    "data": [],
                    "message": f"Missing Jira configuration: {', '.join(missing)}",
                }
            ),
            400,
        )

    base_url = _normalize_jira_base_url(current_app.config["JIRA_BASE_URL"])
    comments_url = f"{base_url}/rest/api/3/issue/{ticket_key}/comment"

    try:
        response = requests.get(
            comments_url,
            params={"orderBy": "-created", "maxResults": 100},
            auth=_jira_auth(),
            headers={"Accept": "application/json"},
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        return jsonify({"data": [], "message": f"Unable to reach Jira: {exc}"}), 502

    if response.status_code >= 400:
        details = response.text[:300]
        return (
            jsonify(
                {
                    "data": [],
                    "message": f"Jira API error ({response.status_code}): {details}",
                }
            ),
            response.status_code,
        )

    comments = []
    for comment in response.json().get("comments", []):
        author = comment.get("author") or {}
        comments.append(
            {
                "id": comment.get("id"),
                "author": author.get("displayName"),
                "created": comment.get("created"),
                "updated": comment.get("updated"),
                "body": _adf_to_text(comment.get("body")).strip(),
            }
        )

    return jsonify(
        {
            "data": comments,
            "message": "Jira comments fetched successfully",
            "total": len(comments),
        }
    )


@tickets_bp.route("/<ticket_key>/note", methods=["PUT"])
def save_ticket_note(ticket_key):
    payload = request.get_json(silent=True) or {}
    note_text = (payload.get("note") or "").strip()

    ticket_note = TicketNote.query.filter_by(ticket_key=ticket_key).one_or_none()
    if ticket_note is None:
        ticket_note = TicketNote(ticket_key=ticket_key, note=note_text)
        db.session.add(ticket_note)
    else:
        ticket_note.note = note_text

    db.session.commit()

    return jsonify(
        {
            "data": {
                "ticket_key": ticket_note.ticket_key,
                "note": ticket_note.note,
                "updated_at": ticket_note.updated_at.isoformat(),
            },
            "message": "Scrum note saved successfully",
        }
    )
