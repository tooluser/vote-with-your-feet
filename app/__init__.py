from flask import Flask, redirect, url_for, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from app.config import Config
from app.database import init_db, get_session
from app.models import Poll

socketio = SocketIO()


def create_app(config_class=Config):
    """Flask application factory"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)

    CORS(app)

    init_db(app.config['DATABASE_URL'])

    socketio.init_app(app, cors_allowed_origins="*")

    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        """Redirect to display page"""
        return redirect(url_for('display'))

    @app.route('/display')
    def display():
        """Display page for showing poll results"""
        session = get_session()
        active_poll = session.query(Poll).filter_by(is_active=True).first()

        if active_poll:
            counts = active_poll.get_vote_counts(session)
            return render_template('display.html',
                                 poll=active_poll,
                                 count_a=counts['A'],
                                 count_b=counts['B'])
        else:
            return render_template('display.html', poll=None)

    @app.route('/display-no-votes')
    def display_no_votes():
        """Display page showing poll options without vote counts"""
        session = get_session()
        active_poll = session.query(Poll).filter_by(is_active=True).first()
        return render_template('display_no_votes.html', poll=active_poll)

    @app.route('/display-completed')
    def display_completed():
        """Display page showing completed polls in 2x2 grid"""
        session = get_session()

        # Get all inactive polls, ordered by most recent first
        completed_polls = session.query(Poll).filter_by(
            is_active=False
        ).order_by(Poll.created_at.desc()).all()

        # Get vote counts for each poll
        polls_with_counts = []
        for poll in completed_polls:
            counts = poll.get_vote_counts(session)
            total_votes = counts['A'] + counts['B']

            # Calculate percentages for bar heights
            if total_votes > 0:
                percent_a = (counts['A'] / total_votes) * 100
                percent_b = (counts['B'] / total_votes) * 100
            else:
                percent_a = 0
                percent_b = 0

            polls_with_counts.append({
                'poll': poll,
                'count_a': counts['A'],
                'count_b': counts['B'],
                'percent_a': percent_a,
                'percent_b': percent_b
            })

        return render_template('display_completed.html', polls=polls_with_counts)

    return app

