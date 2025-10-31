from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

class PrefixMiddleware:
    """
    Honor X-Script-Name (from Nginx) by setting SCRIPT_NAME and trimming PATH_INFO.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):] or '/'
        return self.app(environ, start_response)

application = create_app()
# trust proxy headers for scheme/host so url_for builds https URLs correctly
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1)
# honor /vote prefix
application.wsgi_app = PrefixMiddleware(application.wsgi_app)
