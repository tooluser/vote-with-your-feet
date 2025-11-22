import pytest
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models import Base, Poll, Vote


@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def describe_poll_model():
    
    def it_creates_poll_with_question_and_two_answers(db_session):
        poll = Poll(
            question="What is your favorite color?",
            answer_a="Red",
            answer_b="Blue"
        )
        db_session.add(poll)
        db_session.commit()
        
        assert poll.id is not None
        assert poll.question == "What is your favorite color?"
        assert poll.answer_a == "Red"
        assert poll.answer_b == "Blue"
        assert poll.is_active is False
        assert isinstance(poll.created_at, datetime)
    
    def it_activates_and_deactivates_polls(db_session):
        poll = Poll(
            question="Test question?",
            answer_a="Option A",
            answer_b="Option B"
        )
        db_session.add(poll)
        db_session.commit()
        
        assert poll.is_active is False
        
        poll.is_active = True
        db_session.commit()
        assert poll.is_active is True
        
        poll.is_active = False
        db_session.commit()
        assert poll.is_active is False
    
    def it_only_allows_one_active_poll_at_a_time(db_session):
        poll1 = Poll(question="Q1?", answer_a="A1", answer_b="B1", is_active=True)
        poll2 = Poll(question="Q2?", answer_a="A2", answer_b="B2")
        poll3 = Poll(question="Q3?", answer_a="A3", answer_b="B3")
        
        db_session.add_all([poll1, poll2, poll3])
        db_session.commit()
        
        Poll.activate_poll(db_session, poll2.id)
        db_session.commit()
        
        db_session.refresh(poll1)
        db_session.refresh(poll2)
        db_session.refresh(poll3)
        
        assert poll1.is_active is False
        assert poll2.is_active is True
        assert poll3.is_active is False
    
    def it_calculates_vote_counts_for_answers(db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B")
        db_session.add(poll)
        db_session.commit()
        
        vote1 = Vote(poll_id=poll.id, answer="A")
        vote2 = Vote(poll_id=poll.id, answer="A")
        vote3 = Vote(poll_id=poll.id, answer="B")
        
        db_session.add_all([vote1, vote2, vote3])
        db_session.commit()
        
        counts = poll.get_vote_counts(db_session)
        assert counts["A"] == 2
        assert counts["B"] == 1


def describe_vote_model():
    
    def it_creates_vote_for_poll_with_answer_a_or_b(db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B")
        db_session.add(poll)
        db_session.commit()
        
        vote_a = Vote(poll_id=poll.id, answer="A")
        vote_b = Vote(poll_id=poll.id, answer="B")
        
        db_session.add_all([vote_a, vote_b])
        db_session.commit()
        
        assert vote_a.id is not None
        assert vote_a.answer == "A"
        assert vote_b.id is not None
        assert vote_b.answer == "B"
    
    def it_requires_valid_poll_id(db_session):
        vote = Vote(poll_id=999, answer="A")
        db_session.add(vote)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def it_auto_generates_timestamp(db_session):
        poll = Poll(question="Test?", answer_a="A", answer_b="B")
        db_session.add(poll)
        db_session.commit()
        
        vote = Vote(poll_id=poll.id, answer="A")
        db_session.add(vote)
        db_session.commit()
        
        assert vote.timestamp is not None
        assert isinstance(vote.timestamp, datetime)

