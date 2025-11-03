from flask import Flask, g, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from datetime import date
from zoneinfo import ZoneInfo
from markupsafe import Markup
import os
import markdown as md

# --- Locale / time ---
REYKJAVIK = ZoneInfo("Atlantic/Reykjavik")
_IS_MONTHS = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "maí", 6: "jún",
    7: "júl", 8: "ágú", 9: "sep", 10: "okt", 11: "nóv", 12: "des"
}

def utc_to_local_human(dt):
    if not dt:
        return ""
    dt = dt.astimezone(REYKJAVIK)
    # e.g. "2. nóv 2025 kl. 22:00"
    return f"{dt.day}. {_IS_MONTHS[dt.month]} {dt.year} kl. {dt:%H:%M}"

def utc_to_local_minutes(dt):
    if not dt:
        return ""
    return (
        dt.astimezone(REYKJAVIK)
          .replace(second=0, microsecond=0)
          .strftime("%Y-%m-%dT%H:%M")
    )

def markdown_filter(text):
    if not text:
        return ""
    html = md.markdown(
        text,
        extensions=["extra", "tables", "fenced_code", "sane_lists", "nl2br", "smarty"],
    )
    return Markup(html)

db = SQLAlchemy()

def ensure_schema():
    # Create tables only if they don't exist (use 'elections' as sentinel)
    insp = inspect(db.engine)
    if not insp.has_table("elections"):
        db.create_all()

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=False,
        static_folder="static",
        # LOCAL: /static (default). PROD: set STATIC_URL_PATH=/vote/static
        static_url_path=os.environ.get("STATIC_URL_PATH", "/static"),
    )
    app.config.from_object("app.config.Config")

    # Make helpers/filters available in Jinja
    app.jinja_env.globals.update(
        date=date,
        utc_to_local_minutes=utc_to_local_minutes,
        utc_to_local_human=utc_to_local_human,
        build_rev=os.environ.get("BUILD_REV", "dev"),
    )
    app.jinja_env.filters["md"] = markdown_filter

    # Robust asset() helper:
    # - full URLs (/^https?:|^data:/) pass through
    # - leading "/static/..." is normalized to url_for('static', ...)
    # - bare paths like "img/foo.svg" are treated as static filenames
    def asset(path: str | None, default: str | None = None) -> str:
        val = path or default
        if not val:
            return ""
        if val.startswith(("http://", "https://", "data:")):
            return val
        if val.startswith("/static/"):
            return url_for("static", filename=val[len("/static/"):])
        return url_for("static", filename=val)
    app.jinja_env.globals["asset"] = asset

    def staticv(filename: str) -> str:
        """Build /static URL with a cache-busting version."""
        return url_for("static", filename=filename, v=os.environ.get("BUILD_REV", "dev"))

    app.jinja_env.globals["staticv"] = staticv

    # Optionally load .env in dev
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
