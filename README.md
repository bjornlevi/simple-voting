
# Election MVC (Flask)

A standard MVC-style Flask app for setting up elections with yes/no or ranked-choice voting.

## Features
- Index lists elections with image (default if none)
- Mock authentication (kennitala) then vote
- 1 option -> yes/no; 2+ options -> ranked choice
- One vote per voter per election (registry)
- Votes contain **no PII** (only election_id, vote JSON, date, hash chain)
- Per-election salt and **hash chain** for immutability
- Admins can create/delete admins and create/delete elections
- Export curated votes (CSV) after election end

## Project layout
```text
app/
  __init__.py
  config.py
  models.py
  controllers/
    main.py      # index, login/logout
    voting.py    # election detail, cast vote, export
    admin.py     # admin dashboard, manage admins/elections
  services/
    auth.py      # mock auth helpers
    hashing.py   # canonicalize + SHA-256 hash chaining
  templates/
    base.html
    index.html
    login.html
    election_detail.html
    admin/
      home.html
      create_election.html
  static/
    css/style.css
run.py
requirements.txt
```

## Running
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY='change-me'
python run.py
```

## First admin
Use the admin panel to add yourself *after* logging in with any kennitala.
Or pre-seed via a one-off script or SQL insert if desired.

## Notes
- Replace the mock login with real SSO and set `session['kennitala']` from the identity provider.
- Consider adding CSRF protection (Flask-WTF) for production forms.
- For serious deployments use Alembic migrations and Postgres.
