
import json
import hashlib
from datetime import UTC

def canonicalize_vote(vote_payload: dict) -> str:
    return json.dumps(vote_payload, sort_keys=True, separators=(",", ":"))

def compute_vote_hash(election_salt: str, canonical_vote: str, prev_hash: str | None) -> str:
    to_hash = f"{prev_hash or ''}|{canonical_vote}|{election_salt}".encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()

def compute_registry_receipt(
    election_id: int,
    kennitala: str,
    timestamp,                    # aware datetime
    *, salt: str | None = None,   # optional election salt
    secret: str | None = None     # optional app SECRET_KEY pepper
) -> str:
    """
    Deterministic receipt for a registry row (no relation to ballot content).
    Normalizes timestamp to UTC seconds to avoid drift.
    """
    ts = timestamp.astimezone(UTC).replace(microsecond=0).isoformat()
    payload = f"REG|{election_id}|{kennitala}|{ts}"
    if salt:
        payload += f"|S:{salt}"
    if secret:
        payload += f"|K:{secret}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()