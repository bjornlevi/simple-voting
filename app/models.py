
from datetime import datetime, UTC, timedelta
import json
from app import db

def _to_aware_utc(dt):
    if dt is None:
        return None
    # If SQLite returned naive, assume it's UTC
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    kennitala = db.Column(db.String(20), unique=True, nullable=False)

class Election(db.Model):
    __tablename__ = 'elections'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    image_url = db.Column(db.String(500), nullable=True)
    options_json = db.Column(db.Text, nullable=False)

    # keep timezone=True for future engines; SQLite still strips it
    start_at = db.Column(db.DateTime(timezone=True), nullable=False)
    end_at   = db.Column(db.DateTime(timezone=True), nullable=False)

    salt = db.Column(db.String(64), nullable=False)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def options(self):
        return json.loads(self.options_json)

    def _aware(self, dt):
        if dt is None: return None
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)

    def is_open(self) -> bool:
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        start = self._aware(self.start_at)
        end   = self._aware(self.end_at)
        closed = self._aware(self.closed_at) if self.closed_at else None
        return (closed is None) and (start <= now <= end)

    def is_upcoming(self) -> bool:
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        start = self._aware(self.start_at)
        return start > now

    def is_recently_finished(self, days: int = 7) -> bool:
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        end = self._aware(self.end_at)
        return end < now and end >= (now - timedelta(days=days))
    
class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    vote_json = db.Column(db.Text, nullable=False)
    vote_date = db.Column(db.Date, nullable=False)
    prev_hash = db.Column(db.String(64), nullable=True)
    vote_hash = db.Column(db.String(64), nullable=False)

class VotingRegistry(db.Model):
    __tablename__ = 'voting_registry'
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    kennitala = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('election_id', 'kennitala', name='uniq_election_voter'),
    )
