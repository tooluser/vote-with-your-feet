from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models import Base

_session = None


def init_db(database_url='sqlite:///votes.db'):
    """Initialize the database"""
    global _session
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    _session = scoped_session(session_factory)
    return engine


def get_session():
    """Get the current database session"""
    return _session

