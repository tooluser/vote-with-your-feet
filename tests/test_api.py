import pytest
import json
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
    
    yield app
    
    Session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db_module._session


def describe_vote_api():
    
    def it_registers_vote_for_active_poll(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()
        
        response = client.post('/api/vote', 
                              data=json.dumps({'answer': 'A'}),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        vote = db_session.query(Vote).first()
        assert vote is not None
        assert vote.poll_id == poll.id
        assert vote.answer == 'A'
    
    def it_rejects_vote_when_no_active_poll(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=False)
        db_session.add(poll)
        db_session.commit()
        
        response = client.post('/api/vote',
                              data=json.dumps({'answer': 'A'}),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'no active poll' in data['error'].lower()
    
    def it_rejects_vote_with_invalid_answer(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()
        
        response = client.post('/api/vote',
                              data=json.dumps({'answer': 'C'}),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['error'].lower()
    
    def it_uses_system_timestamp(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()
        
        client.post('/api/vote',
                   data=json.dumps({'answer': 'A'}),
                   content_type='application/json')
        
        vote = db_session.query(Vote).first()
        assert vote.timestamp is not None

