
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import json, secrets
from app.models import AdminUser, Election, VotingRegistry, Vote
from app.services.auth import is_admin
from app import db

admin_bp = Blueprint("admin", __name__)

def require_admin():
    if not is_admin():
        from flask import abort
        abort(403)

@admin_bp.route("/")
def home():
    require_admin()
    admins = AdminUser.query.order_by(AdminUser.kennitala.asc()).all()
    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template("admin/home.html", admins=admins, elections=elections)

@admin_bp.route("/admins", methods=["POST"])
def admins_mod():
    require_admin()
    action = request.form.get("action")
    kt = request.form.get("kennitala","").strip()
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

@admin_bp.route("/elections/create", methods=["GET","POST"])
def create_election():
    require_admin()
    if request.method == "POST":
        title = request.form.get("title","").strip()
        description = request.form.get("description","").strip()
        image_url = request.form.get("image_url","").strip() or None
        options_raw = request.form.get("options","").strip()
        start_date_str = request.form.get("start_date","")
        end_date_str = request.form.get("end_date","")
        if not (title and options_raw and start_date_str and end_date_str):
            flash("Missing required fields", "error")
            return redirect(url_for("admin.create_election"))
        options = [o.strip() for o in options_raw.split("\n") if o.strip()]
        try:
            sd = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            ed = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Bad date format (YYYY-MM-DD)", "error")
            return redirect(url_for("admin.create_election"))
        if ed < sd:
            flash("End date must be after start date", "error")
            return redirect(url_for("admin.create_election"))
        election = Election(title=title, description=description, image_url=image_url,
                            options_json=json.dumps(options), start_date=sd, end_date=ed, salt=secrets.token_hex(16))
        db.session.add(election)
        db.session.commit()
        flash("Election created", "success")
        return redirect(url_for("admin.home"))
    return render_template("admin/create_election.html")

@admin_bp.route("/elections/<int:election_id>/delete", methods=["POST"])
def delete_election(election_id: int):
    require_admin()
    VotingRegistry.query.filter_by(election_id=election_id).delete()
    Vote.query.filter_by(election_id=election_id).delete()
    Election.query.filter_by(id=election_id).delete()
    db.session.commit()
    flash("Election deleted", "success")
    return redirect(url_for("admin.home"))

from datetime import datetime  # top

@admin_bp.route("/elections/<int:election_id>/close", methods=["POST"])
def close_election(election_id: int):
    require_admin()
    e = Election.query.get_or_404(election_id)
    if e.closed_at is None:
        e.closed_at = datetime.utcnow()
        db.session.commit()
        flash("Election closed now.", "success")
    else:
        flash("Election is already closed.", "error")
    return redirect(url_for("admin.home"))

@admin_bp.route("/elections/<int:election_id>/reopen", methods=["POST"])
def reopen_election(election_id: int):
    require_admin()
    e = Election.query.get_or_404(election_id)
    if e.closed_at is not None:
        e.closed_at = None
        db.session.commit()
        flash("Election reopened.", "success")
    else:
        flash("Election is not closed.", "error")
    return redirect(url_for("admin.home"))
