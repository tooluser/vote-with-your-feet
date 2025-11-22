from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models import Base


def init_db(database_url='sqlite:///votes.db'):
    """Initialize the database"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Create a scoped session"""
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

