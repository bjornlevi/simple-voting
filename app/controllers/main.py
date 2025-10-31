
from flask import Blueprint, render_template, current_app, redirect, url_for, request, flash
from app.models import Election, AdminUser
from app.services import auth
from app import db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template("index.html", elections=elections, default_image=current_app.config["DEFAULT_IMAGE"])

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        kennitala = request.form.get("kennitala", "").strip()
        if not kennitala:
            flash("Please enter kennitala", "error")
            return redirect(url_for("main.login"))
        is_admin = bool(AdminUser.query.filter_by(kennitala=kennitala).first())
        auth.set_authenticated(kennitala, is_admin)
        flash("Logged in", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    auth.logout()
    flash("Logged out", "success")
    return redirect(url_for("main.index"))
