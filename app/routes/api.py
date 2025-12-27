from flask import Blueprint, jsonify, render_template, request

from app.database import get_session
from app.middleware.auth import require_vote_password
from app.models import Poll, Vote
from app.utils.responses import format_poll_response

api_bp = Blueprint("api", __name__, template_folder="../../templates")


@api_bp.route("/vote", methods=["POST"])
@require_vote_password
def vote():
    """Register a vote for the active poll"""
    session = get_session()

    answer = request.args.get("answer")
    if not answer:
        return jsonify({"success": False, "error": "Answer is required"}), 400

    if answer not in ["A", "B"]:
        return (
            jsonify({"success": False, "error": "Invalid answer. Must be A or B"}),
            400,
        )

    active_poll = session.query(Poll).filter_by(is_active=True).first()

    if not active_poll:
        return jsonify({"success": False, "error": "No active poll"}), 400

    vote = Vote(poll_id=active_poll.id, answer=answer)
    session.add(vote)
    session.commit()

    try:
        from app import socketio

        socketio.emit("vote_cast", {"poll_id": active_poll.id})
    except:
        pass

    return jsonify({"success": True, "poll_id": active_poll.id}), 200


@api_bp.route("/display/data")
def display_data():
    """Get current active poll data for display"""
    session = get_session()
    active_poll = session.query(Poll).filter_by(is_active=True).first()

    if not active_poll:
        return jsonify({"poll": None}), 200

    return jsonify(format_poll_response(active_poll, session)), 200
