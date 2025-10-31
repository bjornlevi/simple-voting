
# Mock authentication service.
# In production, replace with real SSO and pull kennitala from the identity token/claims.
from flask import session

def set_authenticated(kennitala: str, is_admin: bool):
    session['kennitala'] = kennitala
    session['is_admin'] = bool(is_admin)

def logout():
    session.clear()

def current_kennitala() -> str | None:
    return session.get('kennitala')

def is_admin() -> bool:
    return bool(session.get('is_admin'))
