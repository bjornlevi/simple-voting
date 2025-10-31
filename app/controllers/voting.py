
from datetime import datetime, date
import json
import csv
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, abort, send_file, current_app, session   # ← add session
)
from app.models import Election, Vote, VotingRegistry
from app.services.auth import current_kennitala
from app.services.hashing import canonicalize_vote, compute_vote_hash
from app import db
import random


voting_bp = Blueprint("voting", __name__)

@voting_bp.route("/<int:election_id>")
def election_detail(election_id: int):
    election = Election.query.get_or_404(election_id)
    if not current_kennitala():
        return redirect(url_for("main.login", next=url_for("voting.election_detail", election_id=election.id)))

    # shuffle options once per user per election, keep stable in session
    key = f"shuffled_options_e{election.id}"
    if key not in session:
        opts = election.options()[:]
        random.shuffle(opts)
        session[key] = opts
    shuffled = session[key]

    already = VotingRegistry.query.filter_by(election_id=election.id, kennitala=current_kennitala()).first()
    return render_template(
        "election_detail.html",
        election=election,
        already=bool(already),
        default_image=current_app.config["DEFAULT_IMAGE"],
        shuffled_options=shuffled,  # NEW
    )

@voting_bp.route("/<int:election_id>/vote", methods=["POST"])
def cast_vote(election_id: int):
    election = Election.query.get_or_404(election_id)
    kt = current_kennitala()
    if not kt:
        return redirect(url_for("main.login", next=url_for("voting.election_detail", election_id=election.id)))

    existing = VotingRegistry.query.filter_by(election_id=election.id, kennitala=kt).first()
    if existing:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.election_detail", election_id=election.id))

    options = election.options()
    if len(options) == 1:
        choice = request.form.get("yesno")
        if choice not in ("YES", "NO"):
            flash("Invalid yes/no vote.", "error")
            return redirect(url_for("voting.election_detail", election_id=election.id))
        vote_payload = {"type": "yesno", "vote": choice, "option": options[0]}
    else:
        # Enforce: non-empty vote, no duplicates, no gaps (contiguous from rank 1)
        seen = set()
        ranking = []

        # require rank_1 chosen
        first = request.form.get("rank_1")
        if not first or first not in options:
            flash("Rank 1 must be selected.", "error")
            return redirect(url_for("voting.election_detail", election_id=election.id))

        encountered_blank = False
        for i in range(1, len(options) + 1):
            val = request.form.get(f"rank_{i}")
            if not val:
                encountered_blank = True
                continue
            # if we already saw a blank, any later non-blank is illegal (no gaps)
            if encountered_blank:
                flash("No gaps allowed: fill earlier ranks before later ones.", "error")
                return redirect(url_for("voting.election_detail", election_id=election.id))
            if val not in options or val in seen:
                flash("Invalid or duplicate ranking.", "error")
                return redirect(url_for("voting.election_detail", election_id=election.id))
            seen.add(val)
            ranking.append(val)

        vote_payload = {"type": "ranked", "ranking": ranking, "options": options}

    canonical = canonicalize_vote(vote_payload)
    prev = db.session.query(Vote.vote_hash).filter_by(election_id=election.id).order_by(Vote.id.desc()).limit(1).scalar()
    vote_hash = compute_vote_hash(election.salt, canonical, prev)

    v = Vote(election_id=election.id, vote_json=canonical, vote_date=date.today(), prev_hash=prev, vote_hash=vote_hash)
    db.session.add(v)
    reg = VotingRegistry(election_id=election.id, kennitala=kt, timestamp=datetime.utcnow())
    db.session.add(reg)
    db.session.commit()

    flash("Vote submitted. Thank you!", "success")
    return redirect(url_for("voting.election_detail", election_id=election.id))

@voting_bp.route("/<int:election_id>/export")
def export_votes(election_id: int):
    election = Election.query.get_or_404(election_id)
    # Block export only if still open
    if election.is_open():
        abort(403, description="Election not finished yet.")    
    if date.today() <= election.end_date:
        abort(403, description="Election not finished yet.")

    votes = Vote.query.filter_by(election_id=election.id).order_by(Vote.id.asc()).all()
    options = election.options()
    tmp_path = f"/mnt/data/election_{election.id}_votes.csv"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if len(options) == 1:
            writer.writerow(["election_id", "vote_date", "type", "question", "vote", "prev_hash", "vote_hash"])
            for v in votes:
                payload = json.loads(v.vote_json)
                writer.writerow([election.id, v.vote_date.isoformat(), payload["type"], payload.get("option",""), payload["vote"], v.prev_hash or "", v.vote_hash])
        else:
            header = ["election_id", "vote_date", "type"] + [f"rank_{i+1}" for i in range(len(options))] + ["prev_hash","vote_hash"]
            writer.writerow(header)
            for v in votes:
                payload = json.loads(v.vote_json)
                ranking = payload.get("ranking", [])
                row = [election.id, v.vote_date.isoformat(), payload["type"]] + ranking + [""] * (len(options)-len(ranking)) + [v.prev_hash or "", v.vote_hash]
                writer.writerow(row)
    return send_file(tmp_path, as_attachment=True, download_name=f"election_{election.id}_votes.csv")
