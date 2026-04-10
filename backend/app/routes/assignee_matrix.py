from flask import Blueprint, jsonify

assignee_matrix_bp = Blueprint("assignee_matrix", __name__)


@assignee_matrix_bp.route("/", methods=["GET"])
def get_assignee_matrix():
    return jsonify({"data": [], "message": "Assignee matrix API placeholder"})
