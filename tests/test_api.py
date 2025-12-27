import json

import pytest
from flask import Flask
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

from app import database as db_module
from app.config import Config
from app.models import Base, Poll, Vote
from app.routes.api import api_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["TESTING"] = True

    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))

    db_module._session = Session

    app.register_blueprint(api_bp, url_prefix="/api")

    yield app

    Session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db_module._session


def describe_vote_api():

    def it_requires_vote_password(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.post("/api/vote?answer=A")

        assert response.status_code == 403

    def it_registers_vote_for_active_poll(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.post(
            "/api/vote?answer=A", headers={"X-Vote-Password": "vote123"}
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response format
        assert "poll" in data
        assert data["poll"]["id"] == poll.id

        # Verify vote was recorded
        vote = db_session.query(Vote).first()
        assert vote is not None
        assert vote.poll_id == poll.id
        assert vote.answer == "A"

    def it_returns_full_poll_data_in_response(client, db_session):
        poll = Poll(
            question="Test Question?",
            answer_a="Option A",
            answer_b="Option B",
            is_active=True
        )
        db_session.add(poll)
        db_session.commit()

        # Add some existing votes
        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()

        response = client.post(
            "/api/vote?answer=B", headers={"X-Vote-Password": "vote123"}
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should match display/data format
        assert "poll" in data
        assert data["poll"]["id"] == poll.id
        assert data["poll"]["question"] == "Test Question?"
        assert data["poll"]["answer_a"] == "Option A"
        assert data["poll"]["answer_b"] == "Option B"
        assert data["poll"]["count_a"] == 2
        assert data["poll"]["count_b"] == 2  # 1 existing + 1 new

    def it_rejects_vote_when_no_active_poll(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=False)
        db_session.add(poll)
        db_session.commit()

        response = client.post(
            "/api/vote?answer=A", headers={"X-Vote-Password": "vote123"}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "no active poll" in data["error"].lower()

    def it_rejects_vote_with_invalid_answer(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        response = client.post(
            "/api/vote?answer=C", headers={"X-Vote-Password": "vote123"}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "invalid" in data["error"].lower()

    def it_uses_system_timestamp(client, db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B", is_active=True)
        db_session.add(poll)
        db_session.commit()

        client.post("/api/vote?answer=A", headers={"X-Vote-Password": "vote123"})

        vote = db_session.query(Vote).first()
        assert vote.timestamp is not None
