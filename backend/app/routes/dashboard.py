from flask import Blueprint, jsonify

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
def dashboard_summary():
    return jsonify({
        "total": 0,
        "status_summary": [],
        "priority_summary": []
    })
