from flask import Blueprint, jsonify


tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/", methods=["GET"])
def get_tickets():
    return jsonify({"data": [], "message": "Ticket API placeholder"})


@tickets_bp.route("/sync", methods=["POST"])
def sync_tickets():
    return jsonify({"message": "Jira sync placeholder"})
