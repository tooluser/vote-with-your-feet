from functools import wraps
from flask import request, current_app, abort


def require_admin_secret(f):
    """Decorator to validate admin secret from query param or header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret_from_query = request.args.get('secret')
        secret_from_header = request.headers.get('X-Admin-Secret')

        expected_secret = current_app.config.get('ADMIN_SECRET')

        if secret_from_query == expected_secret or secret_from_header == expected_secret:
            return f(*args, **kwargs)

        abort(403)

    return decorated_function


def require_vote_password(f):
    """Decorator to validate vote password from header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password_from_header = request.headers.get('X-Vote-Password')
        expected_password = current_app.config.get('VOTE_PASSWORD')

        if password_from_header == expected_password:
            return f(*args, **kwargs)

        abort(403)

    return decorated_function

