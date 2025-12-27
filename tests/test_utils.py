import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

from app.models import Base, Poll, Vote
from app.utils.responses import format_poll_response


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    yield Session
    Session.remove()


def describe_format_poll_response():

    def it_formats_poll_with_vote_counts(db_session):
        poll = Poll(
            id=1,
            question="Test Question?",
            answer_a="Option A",
            answer_b="Option B",
            is_active=True
        )
        db_session.add(poll)
        db_session.commit()

        # Add some votes
        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()

        result = format_poll_response(poll, db_session)

        assert result == {
            "poll": {
                "id": 1,
                "question": "Test Question?",
                "answer_a": "Option A",
                "answer_b": "Option B",
                "count_a": 2,
                "count_b": 1
            }
        }

    def it_handles_poll_with_no_votes(db_session):
        poll = Poll(
            id=2,
            question="New Question?",
            answer_a="Yes",
            answer_b="No",
            is_active=True
        )
        db_session.add(poll)
        db_session.commit()

        result = format_poll_response(poll, db_session)

        assert result == {
            "poll": {
                "id": 2,
                "question": "New Question?",
                "answer_a": "Yes",
                "answer_b": "No",
                "count_a": 0,
                "count_b": 0
            }
        }
