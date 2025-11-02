
# Mock authentication service.
# In production, replace with real SSO and pull kennitala from the identity token/claims.
from flask import session
from functools import wraps
from flask import g, abort

def set_authenticated(kennitala: str, is_admin: bool):
    session['kennitala'] = kennitala
    session['is_admin'] = bool(is_admin)

def logout():
    session.clear()

def current_kennitala() -> str | None:
    return session.get('kennitala')

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "is_admin", False):
            return abort(403)
        return view(*args, **kwargs)
    return wrapped