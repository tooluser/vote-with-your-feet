from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware.auth import require_admin_secret
from app.database import get_session
from app.models import Poll

admin_bp = Blueprint('admin', __name__, template_folder='../../templates')


@admin_bp.route('/')
@require_admin_secret
def index():
    """Admin page showing all polls with vote counts"""
    session = get_session()
    polls = session.query(Poll).order_by(Poll.created_at.desc()).all()

    polls_with_counts = []
    for poll in polls:
        counts = poll.get_vote_counts(session)
        polls_with_counts.append({
            'poll': poll,
            'count_a': counts['A'],
            'count_b': counts['B']
        })

    return render_template('admin.html', polls=polls_with_counts)


@admin_bp.route('/polls', methods=['POST'])
@require_admin_secret
def create_poll():
    """Create a new poll"""
    session = get_session()

    question = request.form.get('question', '').strip()
    answer_a = request.form.get('answer_a', '').strip()
    answer_b = request.form.get('answer_b', '').strip()

    if not question or not answer_a or not answer_b:
        flash('All fields are required')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    poll = Poll(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        is_active=False
    )

    session.add(poll)
    session.commit()

    flash('Poll created successfully')
    return redirect(url_for('admin.index', secret=request.args.get('secret')))


@admin_bp.route('/polls/<int:poll_id>/activate', methods=['POST'])
@require_admin_secret
def activate_poll(poll_id):
    """Activate a poll and deactivate all others"""
    session = get_session()

    Poll.activate_poll(session, poll_id)
    session.commit()

    try:
        from app import socketio
        socketio.emit('poll_activated', {'poll_id': poll_id})
    except:
        pass

    flash('Poll activated')
    return redirect(url_for('admin.index', secret=request.args.get('secret')))


@admin_bp.route('/test')
@require_admin_secret
def test_route():
    """Test route to verify authentication"""
    return 'Admin Test Route', 200

