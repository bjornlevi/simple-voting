
import json
import hashlib

def canonicalize_vote(vote_payload: dict) -> str:
    return json.dumps(vote_payload, sort_keys=True, separators=(",", ":"))

def compute_vote_hash(election_salt: str, canonical_vote: str, prev_hash: str | None) -> str:
    to_hash = f"{prev_hash or ''}|{canonical_vote}|{election_salt}".encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()
