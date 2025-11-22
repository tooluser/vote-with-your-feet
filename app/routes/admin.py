from flask import Blueprint, render_template
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


@admin_bp.route('/test')
@require_admin_secret
def test_route():
    """Test route to verify authentication"""
    return 'Admin Test Route', 200

