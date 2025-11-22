import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")
    VOTE_PASSWORD = os.getenv("VOTE_PASSWORD", "vote123")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///votes.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
