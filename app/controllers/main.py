from datetime import datetime, UTC, timedelta
from flask import Blueprint, render_template, current_app, redirect, url_for, request, flash
from app.models import Election, AdminUser
from app.services import auth
from app import db
from audkenni import see_some_id

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    grace = timedelta(days=14)

    # Show: all open or upcoming elections, plus those that ended within last 14 days
    elections = (Election.query
        .filter(Election.end_at >= (now - grace))
        .order_by(Election.start_at.desc(), Election.id.desc())
        .all()
    )
    return render_template(
        "index.html",
        elections=elections,
        default_image=current_app.config["DEFAULT_IMAGE"],
    )

PURPOSE = "Kosningakerfi Pírata"

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if not phone:
            flash("Sláðu inn símanúmer", "error")
            return redirect(url_for("main.login"))

        try:
            person = see_some_id(phone, PURPOSE)
        except Exception as e:
            flash("Innskráning tókst ekki"+str(e), "error")
            # (Optionally show a more specific message in logs only)
            return render_template("login.html", form={"phone": phone})

        ssn = person["nationalRegisterId"]
        name = person["name"]
        signature = person["signature"]

        is_admin = bool(AdminUser.query.filter_by(kennitala=ssn).first())
        auth.set_authenticated(person, is_admin)
        flash("Innskráning tókst", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)

    return render_template("login.html")

#
#@main_bp.route("/login", methods=["GET", "POST"])
#def login():
#    if request.method == "POST":
#        kennitala = request.form.get("kennitala", "").strip()
#        if not kennitala:
#            flash("Please enter kennitala", "error")
#            return redirect(url_for("main.login"))
#        is_admin = bool(AdminUser.query.filter_by(kennitala=kennitala).first())
#        auth.set_authenticated(kennitala, is_admin)
#        flash("Logged in", "success")
#        next_url = request.args.get("next") or url_for("main.index")
#        return redirect(next_url)
#    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    auth.logout()
    flash("Logged out", "success")
    return redirect(url_for("main.index"))
