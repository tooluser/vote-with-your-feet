import pytest
from flask import Flask
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from app.routes.admin import admin_bp
from app.config import Config
from app.models import Base, Poll, Vote
from app import database as db_module


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['ADMIN_SECRET'] = 'test-secret'
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
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    yield app
    
    Session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db_module._session


def describe_admin_authentication():
    
    def it_requires_secret_query_parameter_or_header(client):
        response = client.get('/admin/test')
        assert response.status_code == 403
    
    def it_rejects_requests_without_valid_secret(client):
        response = client.get('/admin/test?secret=wrong-secret')
        assert response.status_code == 403
        
        response = client.get('/admin/test', headers={'X-Admin-Secret': 'wrong-secret'})
        assert response.status_code == 403
    
    def it_allows_access_with_valid_secret(client):
        response = client.get('/admin/test?secret=test-secret')
        assert response.status_code == 200
        assert b'Admin Test Route' in response.data
        
        response = client.get('/admin/test', headers={'X-Admin-Secret': 'test-secret'})
        assert response.status_code == 200
        assert b'Admin Test Route' in response.data


def describe_admin_poll_listing():
    
    def it_lists_all_polls_with_vote_counts(client, db_session):
        poll1 = Poll(question="Question 1?", answer_a="A1", answer_b="B1")
        poll2 = Poll(question="Question 2?", answer_a="A2", answer_b="B2")
        db_session.add_all([poll1, poll2])
        db_session.commit()
        
        vote1 = Vote(poll_id=poll1.id, answer="A")
        vote2 = Vote(poll_id=poll1.id, answer="B")
        db_session.add_all([vote1, vote2])
        db_session.commit()
        
        response = client.get('/admin/?secret=test-secret')
        assert response.status_code == 200
        assert b'Question 1?' in response.data
        assert b'Question 2?' in response.data
        assert b'A1' in response.data
        assert b'B1' in response.data
    
    def it_highlights_active_poll_visually(client, db_session):
        poll1 = Poll(question="Active Poll?", answer_a="A", answer_b="B", is_active=True)
        poll2 = Poll(question="Inactive Poll?", answer_a="C", answer_b="D")
        db_session.add_all([poll1, poll2])
        db_session.commit()
        
        response = client.get('/admin/?secret=test-secret')
        assert response.status_code == 200
        assert b'poll-active' in response.data or b'ACTIVE' in response.data
    
    def it_shows_zero_votes_for_new_polls(client, db_session):
        poll = Poll(question="New Poll?", answer_a="A", answer_b="B")
        db_session.add(poll)
        db_session.commit()
        
        response = client.get('/admin/?secret=test-secret')
        assert response.status_code == 200
        assert b'New Poll?' in response.data
    
    def it_requires_authentication(client):
        response = client.get('/admin/', follow_redirects=False)
        assert response.status_code == 403

