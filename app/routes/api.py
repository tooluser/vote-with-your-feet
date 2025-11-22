from flask import Blueprint, request, jsonify
from app.database import get_session
from app.models import Poll, Vote

api_bp = Blueprint('api', __name__)


@api_bp.route('/vote', methods=['POST'])
def vote():
    """Register a vote for the active poll"""
    session = get_session()
    
    data = request.get_json()
    if not data or 'answer' not in data:
        return jsonify({'success': False, 'error': 'Answer is required'}), 400
    
    answer = data['answer']
    
    if answer not in ['A', 'B']:
        return jsonify({'success': False, 'error': 'Invalid answer. Must be A or B'}), 400
    
    active_poll = session.query(Poll).filter_by(is_active=True).first()
    
    if not active_poll:
        return jsonify({'success': False, 'error': 'No active poll'}), 400
    
    vote = Vote(poll_id=active_poll.id, answer=answer)
    session.add(vote)
    session.commit()
    
    return jsonify({'success': True, 'poll_id': active_poll.id}), 200

