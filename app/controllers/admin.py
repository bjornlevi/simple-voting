from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
import json, secrets

from app.models import AdminUser, Election, VotingRegistry, Vote
from app.services.auth import admin_required
from app import db

admin_bp = Blueprint("admin", __name__)

# Local-time handling (browser sends local time via datetime-local)
REYKJAVIK = ZoneInfo("Atlantic/Reykjavik")
DT_LOCAL_FMT = "%Y-%m-%dT%H:%M"

def parse_local_to_utc(value: str):
    """Parse 'YYYY-MM-DDTHH:MM' as Reykjavik local, convert to aware UTC."""
    if not value:
        return None
    naive = datetime.strptime(value, DT_LOCAL_FMT)
    local = naive.replace(tzinfo=REYKJAVIK).replace(second=0, microsecond=0)
    return local.astimezone(UTC)

@admin_bp.route("/")
@admin_required
def home():
    admins = AdminUser.query.order_by(AdminUser.kennitala.asc()).all()
    elections = Election.query.order_by(Election.start_at.desc()).all()
    return render_template(
        "admin/home.html", 
        admins=admins, 
        elections=elections, 
        default_image=current_app.config["DEFAULT_IMAGE"],)

@admin_bp.route("/admins", methods=["POST"])
@admin_required
def admins_mod():
    action = request.form.get("action")
    kt = request.form.get("kennitala", "").strip()
    if not kt:
        flash("Kennitala required", "error")
        return redirect(url_for("admin.home"))
    if action == "add":
        if not AdminUser.query.filter_by(kennitala=kt).first():
            db.session.add(AdminUser(kennitala=kt))
            db.session.commit()
            flash("Admin added", "success")
    elif action == "delete":
        # prevent self-delete
        from flask import session
        me = session.get('kennitala')
        if kt == me:
            flash("Cannot delete yourself", "error")
        else:
            AdminUser.query.filter_by(kennitala=kt).delete()
            db.session.commit()
            flash("Admin deleted", "success")
    return redirect(url_for("admin.home"))

@admin_bp.route("/elections/create", methods=["GET", "POST"])
@admin_required
def create_election():
    if request.method == "POST":
        title = request.form.get("title","").strip()
        description = request.form.get("description","").strip()
        image_url = request.form.get("image_url","").strip() or None
        options_raw = request.form.get("options","").strip()

        # NEW: datetime-local fields
        start_at_str = request.form.get("start_at","")
        end_at_str   = request.form.get("end_at","")

        if not (title and options_raw and start_at_str and end_at_str):
            flash("Missing required fields", "error")
            return redirect(url_for("admin.create_election"))

        options = [o.strip() for o in options_raw.split("\n") if o.strip()]

        start_at = parse_local_to_utc(start_at_str)
        end_at   = parse_local_to_utc(end_at_str)
        if not start_at or not end_at:
            flash("Start and end time are required.", "error")
            return redirect(url_for("admin.create_election"))
        if end_at <= start_at:
            flash("End time must be after start time", "error")
            return redirect(url_for("admin.create_election"))

        cutoff_str = request.form.get("eligibility_cutoff","").strip()
        cutoff_date = None
        if cutoff_str:
            try:
                cutoff_date = datetime.strptime(cutoff_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Gjaldgengi: ógilt dagsetningaform (YYYY-MM-DD)", "error")
                return redirect(url_for("admin.create_election"))

        election = Election(
            title=title, description=description, image_url=image_url,
            options_json=json.dumps(options),
            start_at=start_at, end_at=end_at,
            eligibility_cutoff=cutoff_date,  # NEW
            salt=secrets.token_hex(16),
        )
        db.session.add(election)
        db.session.commit()
        flash("Election created", "success")
        return redirect(url_for("admin.home"))

    return render_template("admin/create_election.html")

@admin_bp.route("/elections/<int:election_id>/delete", methods=["POST"])
@admin_required
def delete_election(election_id: int):
    VotingRegistry.query.filter_by(election_id=election_id).delete()
    Vote.query.filter_by(election_id=election_id).delete()
    Election.query.filter_by(id=election_id).delete()
    db.session.commit()
    flash("Election deleted", "success")
    return redirect(url_for("admin.home"))

@admin_bp.route("/elections/<int:election_id>/close", methods=["POST"])
@admin_required
def close_election(election_id: int):
    e = Election.query.get_or_404(election_id)
    if e.closed_at is None:
        e.closed_at = datetime.now(UTC).replace(second=0, microsecond=0)
        db.session.commit()
        flash("Election closed now.", "success")
    else:
        flash("Election is already closed.", "error")
    return redirect(url_for("admin.home"))

@admin_bp.route("/elections/<int:election_id>/reopen", methods=["POST"])
@admin_required
def reopen_election(election_id: int):
    e = Election.query.get_or_404(election_id)
    if e.closed_at is not None:
        e.closed_at = None
        db.session.commit()
        flash("Election reopened.", "success")
    else:
        flash("Election is not closed.", "error")
    return redirect(url_for("admin.home"))
