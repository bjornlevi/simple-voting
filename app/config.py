# app/config.py
import os
from dotenv import load_dotenv
load_dotenv()  # ← ensures .env is loaded before reading os.environ

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///elections.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_IMAGE = os.environ.get("DEFAULT_IMAGE", "img/default_election_clean_dark.svg")
    ICEPIRATE_BASE = os.getenv("ICEPIRATE_BASE", "https://member.piratar.is")
    ICEPIRATE_API_KEY = os.getenv("ICEPIRATE_API_KEY", "")
    ICEPIRATE_FIELD = os.getenv("ICEPIRATE_FIELD", "ssn")
    USE_ICEPIRATE = _env_bool("USE_ICEPIRATE", False)
