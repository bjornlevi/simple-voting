# wsgi.py
from app import create_app

# WSGI entrypoint
application = create_app()
