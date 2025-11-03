# app/controllers/voting.py
from datetime import datetime, date, UTC
import json, csv, random, os
from pathlib import Path
from sqlalchemy.engine import make_url
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, abort, send_file, current_app, session
)
from app.models import Election, Vote, VotingRegistry
from app.services.auth import current_kennitala
from app.services.hashing import canonicalize_vote, compute_vote_hash
from app import db

voting_bp = Blueprint("voting", __name__)

def _export_dir() -> Path:
    """Return <directory containing the DB>/election_exports (create if missing)."""
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    url = make_url(uri)

    # Default base: instance path (works for non-SQLite or unknowns)
    base_dir = Path(current_app.instance_path)

    # If SQLite file, use its actual on-disk directory
    if url.drivername.startswith("sqlite") and url.database:
        db_path = Path(url.database)
        if not db_path.is_absolute():
            # Try resolving relative to instance_path first; fallback to CWD
            candidate = (Path(current_app.instance_path) / db_path)
            db_path = candidate.resolve() if candidate.parent.exists() else db_path.resolve()
        base_dir = db_path.parent

    out = base_dir / "election_exports"
    out.mkdir(parents=True, exist_ok=True)
    return out

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
        shuffled_options=shuffled,
    )

@voting_bp.route("/<int:election_id>/vote", methods=["POST"])
def cast_vote(election_id: int):
    election = Election.query.get_or_404(election_id)
    kt = current_kennitala()
    if not kt:
        return redirect(url_for("main.login", next=url_for("voting.election_detail", election_id=election.id)))

    # NEW: only allow voting while the election is open
    if not election.is_open():
        flash("This election is not accepting votes at this time.", "error")
        return redirect(url_for("voting.election_detail", election_id=election.id))

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

    # Keep vote_date as a date (legacy), but timestamps should be aware UTC
    v = Vote(
        election_id=election.id,
        vote_json=canonical,
        vote_date=date.today(),
        prev_hash=prev,
        vote_hash=vote_hash,
    )
    db.session.add(v)

    reg = VotingRegistry(
        election_id=election.id,
        kennitala=kt,
        timestamp=datetime.now(UTC).replace(second=0, microsecond=0),  # UPDATED
    )
    db.session.add(reg)

    db.session.commit()
    flash("Vote submitted. Thank you!", "success")
    return redirect(url_for("voting.election_detail", election_id=election.id))

@voting_bp.route("/<int:election_id>/export")
def export_votes(election_id: int):
    election = Election.query.get_or_404(election_id)

    # Block export while election is open
    if election.is_open():
        abort(403, description="Election not finished yet.")

    votes = Vote.query.filter_by(election_id=election.id).order_by(Vote.id.asc()).all()
    options = election.options()

    # --- sanitize helper: remove internal CR/LF and trim ---
    def safe_cell(val):
        if val is None:
            return ""
        if isinstance(val, str):
            # collapse any CR/LF inside labels into a single space
            return " ".join(val.replace("\r", "").splitlines()).strip()
        return val

    # write to the exports folder next to the DB
    export_dir: Path = _export_dir()
    tmp_path: Path = export_dir / f"election_{election.id}_votes.csv"

    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)

        if len(options) == 1:
            writer.writerow(["election_id", "vote_date", "type", "question", "vote", "prev_hash", "vote_hash"])
            for v in votes:
                payload = json.loads(v.vote_json)
                row = [
                    election.id,
                    v.vote_date.isoformat(),
                    safe_cell(payload.get("type")),
                    safe_cell(payload.get("option", "")),
                    safe_cell(payload.get("vote", "")),
                    safe_cell(v.prev_hash or ""),
                    safe_cell(v.vote_hash),
                ]
                writer.writerow(row)
        else:
            header = ["election_id", "vote_date", "type"] + [f"rank_{i+1}" for i in range(len(options))] + ["prev_hash","vote_hash"]
            writer.writerow(header)
            for v in votes:
                payload = json.loads(v.vote_json)
                ranking = [safe_cell(x) for x in payload.get("ranking", [])]
                # pad to fixed width
                ranking += [""] * (len(options) - len(ranking))
                row = [
                    election.id,
                    v.vote_date.isoformat(),
                    safe_cell(payload.get("type")),
                    *ranking,
                    safe_cell(v.prev_hash or ""),
                    safe_cell(v.vote_hash),
                ]
                writer.writerow(row)

    return send_file(str(tmp_path), as_attachment=True,
                     download_name=f"election_{election.id}_votes.csv")
