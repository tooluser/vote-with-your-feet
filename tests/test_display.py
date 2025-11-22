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

