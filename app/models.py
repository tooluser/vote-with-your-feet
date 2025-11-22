from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Poll(Base):
    __tablename__ = 'polls'
    
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    answer_a = Column(String, nullable=False)
    answer_b = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    votes = relationship('Vote', back_populates='poll', cascade='all, delete-orphan')
    
    @staticmethod
    def activate_poll(session, poll_id):
        """Activate a poll and deactivate all others"""
        session.query(Poll).update({'is_active': False})
        poll = session.query(Poll).filter_by(id=poll_id).first()
        if poll:
            poll.is_active = True
    
    def get_vote_counts(self, session):
        """Get vote counts for this poll"""
        votes_a = session.query(func.count(Vote.id)).filter_by(
            poll_id=self.id, answer='A'
        ).scalar() or 0
        
        votes_b = session.query(func.count(Vote.id)).filter_by(
            poll_id=self.id, answer='B'
        ).scalar() or 0
        
        return {'A': votes_a, 'B': votes_b}
    
    def __repr__(self):
        return f'<Poll {self.id}: {self.question}>'


class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'), nullable=False)
    answer = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    poll = relationship('Poll', back_populates='votes')
    
    def __repr__(self):
        return f'<Vote {self.id}: Poll {self.poll_id} -> {self.answer}>'

