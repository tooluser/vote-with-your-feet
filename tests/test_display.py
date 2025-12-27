import pytest
from flask import Flask
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from app.routes.api import api_bp
from app.config import Config
from app.models import Base, Poll, Vote
from app import database as db_module


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['TESTING'] = True

    engine = create_engine('sqlite:///:memory:')

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))

    db_module._session = Session

    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/display')
    def display():
        from flask import render_template
        session = db_module._session
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
        from flask import render_template
        session = db_module._session
        active_poll = session.query(Poll).filter_by(is_active=True).first()
        return render_template('display_no_votes.html', poll=active_poll)

    @app.route('/display-completed')
    def display_completed():
        """Display page showing completed polls in 2x2 grid"""
        from flask import render_template
        session = db_module._session

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

    yield app

    Session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db_module._session


def describe_display_interface():

    def it_shows_active_poll_with_split_view(client, db_session):
        poll = Poll(question="Test Question?", answer_a="Option A",
                   answer_b="Option B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.get('/display')
        assert response.status_code == 200
        assert b'Test Question?' in response.data
        assert b'Option A' in response.data
        assert b'Option B' in response.data

    def it_displays_vote_counts_for_each_answer(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()

        response = client.get('/display')
        assert response.status_code == 200
        assert b'2' in response.data
        assert b'1' in response.data

    def it_shows_message_when_no_active_poll(client, db_session):
        poll = Poll(question="Inactive", answer_a="A", answer_b="B", is_active=False)
        db_session.add(poll)
        db_session.commit()

        response = client.get('/display')
        assert response.status_code == 200
        assert b'No active poll' in response.data or b'no poll' in response.data.lower()


def describe_display_no_votes_interface():

    def it_shows_active_poll_question_and_answers(client, db_session):
        poll = Poll(question="What is best?", answer_a="Option A",
                   answer_b="Option B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.get('/display-no-votes')
        assert response.status_code == 200
        assert b'What is best?' in response.data
        assert b'Option A' in response.data
        assert b'Option B' in response.data

    def it_does_not_show_vote_counts(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()

        response = client.get('/display-no-votes')
        assert response.status_code == 200
        assert b'vote-count' not in response.data

    def it_does_not_show_vertical_bars(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.get('/display-no-votes')
        assert response.status_code == 200
        assert b'vertical-bar' not in response.data

    def it_shows_message_when_no_active_poll(client, db_session):
        poll = Poll(question="Inactive", answer_a="A", answer_b="B", is_active=False)
        db_session.add(poll)
        db_session.commit()

        response = client.get('/display-no-votes')
        assert response.status_code == 200
        assert b'No active poll' in response.data or b'no poll' in response.data.lower()


def describe_completed_polls_display():

    def it_shows_2x2_grid_of_completed_polls(client, db_session):
        # Create 4 completed polls
        poll1 = Poll(question="Completed 1?", answer_a="A1", answer_b="B1", is_active=False)
        poll2 = Poll(question="Completed 2?", answer_a="A2", answer_b="B2", is_active=False)
        poll3 = Poll(question="Completed 3?", answer_a="A3", answer_b="B3", is_active=False)
        poll4 = Poll(question="Completed 4?", answer_a="A4", answer_b="B4", is_active=False)
        db_session.add_all([poll1, poll2, poll3, poll4])
        db_session.commit()

        response = client.get("/display-completed")
        assert response.status_code == 200
        assert b"Completed 1?" in response.data
        assert b"Completed 2?" in response.data
        assert b"Completed 3?" in response.data
        assert b"Completed 4?" in response.data

    def it_shows_vote_counts_for_completed_polls(client, db_session):
        poll = Poll(question="Past Poll?", answer_a="Yes", answer_b="No", is_active=False)
        db_session.add(poll)
        db_session.commit()

        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()

        response = client.get("/display-completed")
        assert response.status_code == 200
        assert b"Past Poll?" in response.data
        # Check that counts are present in some form
        assert b"2" in response.data  # count_a
        assert b"1" in response.data or b"3" in response.data  # count_b or total

    def it_excludes_active_polls(client, db_session):
        active_poll = Poll(question="Active?", answer_a="A", answer_b="B", is_active=True)
        completed_poll = Poll(question="Completed?", answer_a="C", answer_b="D", is_active=False)
        db_session.add_all([active_poll, completed_poll])
        db_session.commit()

        response = client.get("/display-completed")
        assert response.status_code == 200
        assert b"Completed?" in response.data
        assert b"Active?" not in response.data

    def it_shows_message_when_no_completed_polls(client, db_session):
        active_poll = Poll(question="Active?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(active_poll)
        db_session.commit()

        response = client.get("/display-completed")
        assert response.status_code == 200
        assert b"No completed polls" in response.data or b"no polls" in response.data.lower()

    def it_orders_polls_by_most_recent(client, db_session):
        from datetime import datetime, timedelta

        # Create polls with different timestamps
        old_poll = Poll(question="Old?", answer_a="A", answer_b="B", is_active=False)
        old_poll.created_at = datetime.utcnow() - timedelta(days=7)

        recent_poll = Poll(question="Recent?", answer_a="C", answer_b="D", is_active=False)
        recent_poll.created_at = datetime.utcnow() - timedelta(days=1)

        db_session.add_all([old_poll, recent_poll])
        db_session.commit()

        response = client.get("/display-completed")
        assert response.status_code == 200

        # Recent should appear before old in the HTML
        recent_pos = response.data.find(b"Recent?")
        old_pos = response.data.find(b"Old?")
        assert recent_pos < old_pos

