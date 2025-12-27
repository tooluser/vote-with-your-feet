from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware.auth import require_admin_secret
from app.database import get_session
from app.models import Poll, Vote

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


@admin_bp.route('/polls/<int:poll_id>/delete', methods=['POST'])
@require_admin_secret
def delete_poll(poll_id):
    """Delete a poll and its associated votes"""
    session = get_session()

    poll = session.query(Poll).filter_by(id=poll_id).first()

    if not poll:
        flash('Poll not found')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    if poll.is_active:
        flash('Cannot delete active poll. Deactivate it first.')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    session.delete(poll)
    session.commit()

    flash('Poll deleted successfully')
    return redirect(url_for('admin.index', secret=request.args.get('secret')))


@admin_bp.route('/polls/<int:poll_id>/edit', methods=['GET'])
@require_admin_secret
def edit_poll(poll_id):
    """Show edit form for a poll"""
    session = get_session()

    poll = session.query(Poll).filter_by(id=poll_id).first()

    if not poll:
        flash('Poll not found')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    return render_template('admin_edit_poll.html', poll=poll)


@admin_bp.route('/polls/<int:poll_id>/edit', methods=['POST'])
@require_admin_secret
def update_poll(poll_id):
    """Update poll text fields"""
    session = get_session()

    poll = session.query(Poll).filter_by(id=poll_id).first()

    if not poll:
        flash('Poll not found')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    question = request.form.get('question', '').strip()
    answer_a = request.form.get('answer_a', '').strip()
    answer_b = request.form.get('answer_b', '').strip()

    if not question or not answer_a or not answer_b:
        flash('All fields are required')
        return render_template('admin_edit_poll.html', poll=poll)

    poll.question = question
    poll.answer_a = answer_a
    poll.answer_b = answer_b

    session.commit()

    flash('Poll updated successfully')
    return redirect(url_for('admin.index', secret=request.args.get('secret')))


@admin_bp.route('/polls/<int:poll_id>/edit-votes', methods=['GET'])
@require_admin_secret
def edit_votes(poll_id):
    """Show edit form for vote counts"""
    session = get_session()

    poll = session.query(Poll).filter_by(id=poll_id).first()

    if not poll:
        flash('Poll not found')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    counts = poll.get_vote_counts(session)

    return render_template(
        'admin_edit_votes.html',
        poll=poll,
        count_a=counts['A'],
        count_b=counts['B']
    )


@admin_bp.route('/polls/<int:poll_id>/edit-votes', methods=['POST'])
@require_admin_secret
def update_votes(poll_id):
    """Update vote counts by adding or removing Vote records"""
    session = get_session()

    poll = session.query(Poll).filter_by(id=poll_id).first()

    if not poll:
        flash('Poll not found')
        return redirect(url_for('admin.index', secret=request.args.get('secret')))

    try:
        new_count_a = int(request.form.get('count_a', 0))
        new_count_b = int(request.form.get('count_b', 0))
    except ValueError:
        flash('Vote counts must be valid numbers')
        counts = poll.get_vote_counts(session)
        return render_template(
            'admin_edit_votes.html',
            poll=poll,
            count_a=counts['A'],
            count_b=counts['B']
        )

    if new_count_a < 0 or new_count_b < 0:
        flash('Vote counts must be non-negative')
        counts = poll.get_vote_counts(session)
        return render_template(
            'admin_edit_votes.html',
            poll=poll,
            count_a=counts['A'],
            count_b=counts['B']
        )

    # Get current counts
    current_counts = poll.get_vote_counts(session)
    current_a = current_counts['A']
    current_b = current_counts['B']

    # Delete all existing votes for this poll
    session.query(Vote).filter_by(poll_id=poll_id).delete()

    # Add new votes to match desired counts
    from datetime import datetime
    for _ in range(new_count_a):
        session.add(Vote(poll_id=poll_id, answer='A'))

    for _ in range(new_count_b):
        session.add(Vote(poll_id=poll_id, answer='B'))

    session.commit()

    flash('Vote counts updated successfully')
    return redirect(url_for('admin.index', secret=request.args.get('secret')))


@admin_bp.route('/test')
@require_admin_secret
def test_route():
    """Test route to verify authentication"""
    return 'Admin Test Route', 200

