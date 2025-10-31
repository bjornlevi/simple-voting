
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('app.config.Config')
    # make `date` available in all templates
    app.jinja_env.globals.update(date=date)

    try:
        from dotenv import load_dotenv
        load_dotenv()  # loads .env from repo root
    except Exception:
        pass

    db.init_app(app)

    with app.app_context():
        from app.controllers.main import main_bp
        from app.controllers.admin import admin_bp
        from app.controllers.voting import voting_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(voting_bp, url_prefix="/elections")

        from app import models  # noqa: F401
        db.create_all()

    return app
