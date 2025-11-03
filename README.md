
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
./.init.sh (and edit the .env file for appropriate values)
python run.py
```

## First admin
Use the admin panel to add yourself *after* logging in with any kennitala.
Or pre-seed via a one-off script or SQL insert if desired.

## Notes
- Replace the mock login with real SSO and set `session['kennitala']` from the identity provider.
- Consider adding CSRF protection (Flask-WTF) for production forms.
- For serious deployments use Alembic migrations and Postgres.

## Election Details (voting flow, receipts, and exports)

The **Election Details** page (`/elections/<id>`) is the main place where a voter views an election, casts a vote (when open), and later sees a receipt and summary.

### Time & state

* All election windows are stored as **UTC** (`start_at`, `end_at`, `closed_at`) and rendered in **Atlantic/Reykjavík**.
* An election exposes three states:

  * **Upcoming** – now < `start_at`.
  * **Open** – `start_at` ≤ now ≤ `end_at` and `closed_at` is `NULL`.
  * **Closed** – `closed_at` is set **or** now > `end_at`.

Helpers:

* `Election.is_open()` — returns `True` only during the open window (aware datetimes).
* `Election.is_upcoming()` — returns `True` before start.
* Templates use `utc_to_local_human(dt)` to show “2. nóv 2025 kl. 22:00”.

### Casting a vote

* User must be authenticated (`kennitala` present in session).
* A user can vote **once per election** (enforced by `VotingRegistry`). No editing of vote allowed. Once cast, it's set.
* Two ballot modes:

  1. **Yes/No** — if the election has exactly one option (treated as a question).
  2. **Ranked** — if the election has 2+ options.

     * The UI enforces: first rank required, no duplicates, no gaps.
     * The page provides a drag-and-drop “pick and rank” interface; options can be reordered or removed.

On submit:

* The ballot is canonicalized and hashed with a per-election `salt` and a chain `prev_hash` (append-only integrity).
* A `Vote` row is stored with `vote_hash` and `prev_hash`.
* A `VotingRegistry` row is stored with `(election_id, kennitala, timestamp)`.

### Vote receipt (privacy-preserving)

After a user has voted, the page shows a **receipt hash** derived only from their **registry** entry (never from ballot content):

```
receipt = SHA256("REG|<election_id>|<kennitala>|<timestamp_utc_seconds>|S:<election_salt>|K:<SECRET_KEY>")
```

* `timestamp` is normalized to UTC seconds to avoid drift.
* Receipt proves the user was recorded in the registry for that election without linking to the ballot.
* The UI shows the hex hash and an **“copy to clipboard”** button.

### After the election (admin & transparency)

When an election is **finished** (closed window):

* The page shows a small summary panel:

  * **Skráningar (VotingRegistry)**: count of registry rows for the election.
  * **Atkvæði (Vote/CSV)**: count of ballots.
* Admins see an **Export CSV** button.

### CSV export

Route: `/elections/<id>/export` (admin only, and only when **not open**).

* Produces a UTF-8 CSV with one of two shapes:

  * **Yes/No**: `election_id, vote_date, type, question, vote, prev_hash, vote_hash`
  * **Ranked**: `election_id, vote_date, type, rank_1..rank_N, prev_hash, vote_hash`
* Export path: `instance/election_exports/election_<id>.csv` (created if missing).
* Export **sanitizes labels** to remove any embedded line breaks or exotic separators so each row is a single physical line.

### Templating overview (what the page renders)

* **Meta tags** show localized start/end:

  * Upcoming: `Kosning hefst: <local start>`
  * Open: `Kosningu lýkur: <local end>`
  * Closed: `Kosningu lokið`
* **Voting UI**:

  * Yes/No: two radios.
  * Ranked: two lists (**Kostir** → **Röðun þín**) with drag-and-drop and small action buttons; long option text wraps fully.
* **Already voted**:

  * Shows the **receipt hash** panel.
* **Closed**:

  * Shows the **registry vs. ballots** summary and the **Export CSV** (admins).

### Developer hooks & config

* **Helpers** exposed to Jinja:

  * `utc_to_local_human(dt)` — formats UTC to “2. nóv 2025 kl. 22:00”.
  * `markdown_filter` (`|md`) — renders election descriptions as Markdown.
  * `is_admin` — injected from `g.is_admin`.
* **Defaults / assets**:

  * `DEFAULT_IMAGE` from `.env` is used if an election has no `image_url`.
* **Storage**:

  * Database is configured via `SQLALCHEMY_DATABASE_URI`.
  * Runtime files (including exports) live under Flask `instance/`.

### Security notes

* No ballot content is used in receipts; receipts are computed from the registry row + salts/secret.
* `admin_required` protects admin routes and close/reopen actions.
* Vote submission requires a valid session (`kennitala`) and checks for **one vote per user per election**.
