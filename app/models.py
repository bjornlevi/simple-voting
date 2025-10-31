
from datetime import date
import json
from app import db

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
    options_json = db.Column(db.Text, nullable=False)  # JSON list of option labels
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    salt = db.Column(db.String(64), nullable=False)

    def options(self):
        return json.loads(self.options_json)

    def is_open(self) -> bool:
        today = date.today()
        return self.start_date <= today <= self.end_date

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
