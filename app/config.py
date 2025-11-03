
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///elections.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_IMAGE = os.environ.get(
        "DEFAULT_IMAGE",
        "img/default_election_clean_dark.svg"
    )
