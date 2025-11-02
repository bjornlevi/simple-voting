from flask import Flask, g, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from datetime import date, UTC
from zoneinfo import ZoneInfo

from datetime import date
from zoneinfo import ZoneInfo
from markupsafe import Markup
import markdown as md

REYKJAVIK = ZoneInfo("Atlantic/Reykjavik")

_IS_MONTHS = {
    1:"jan",2:"feb",3:"mar",4:"apr",5:"maí",6:"jún",
    7:"júl",8:"ágú",9:"sep",10:"okt",11:"nóv",12:"des"
}

def utc_to_local_human(dt):
    if not dt:
        return ""
    dt = dt.astimezone(REYKJAVIK)
    # e.g. "2. nóv 2025 kl. 22:00"
    return f"{dt.day}. {_IS_MONTHS[dt.month]} {dt.year} kl. {dt:%H:%M}"

def markdown_filter(text):
    if not text:
        return ""
    html = md.markdown(
        text,
        extensions=["extra","tables","fenced_code","sane_lists","nl2br","smarty"]
    )
    return Markup(html)  # mark safe for Jinja


db = SQLAlchemy()

def ensure_schema():
    # Create tables only if they don't exist (use 'elections' as sentinel)
    insp = inspect(db.engine)
    if not insp.has_table("elections"):
        db.create_all()

# Jinja helper: format aware UTC -> Reykjavik "YYYY-MM-DDTHH:MM"
def utc_to_local_minutes(dt):
    if not dt:
        return ""
    return (
        dt.astimezone(ZoneInfo("Atlantic/Reykjavik"))
          .replace(second=0, microsecond=0)
          .strftime("%Y-%m-%dT%H:%M")
    )

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('app.config.Config')

    # globals
    app.jinja_env.globals.update(
        date=date,
        utc_to_local_minutes=utc_to_local_minutes,
        utc_to_local_human=utc_to_local_human,
    )
    app.jinja_env.filters["md"] = markdown_filter



    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    db.init_app(app)

    with app.app_context():
        from app import models  # ensure models are registered
        from app.controllers.main import main_bp
        from app.controllers.admin import admin_bp
        from app.controllers.voting import voting_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(voting_bp, url_prefix="/elections")

        ensure_schema()

    @app.before_request
    def load_admin_flag():
        from app.models import AdminUser
        g.is_admin = False
        kt = session.get("kennitala")
        if kt:
            g.is_admin = db.session.query(AdminUser).filter_by(kennitala=kt).first() is not None

    @app.context_processor
    def inject_flags():
        return {"is_admin": bool(getattr(g, "is_admin", False))}

    return app
