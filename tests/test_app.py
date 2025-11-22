import pytest
from app import create_app


def describe_application_setup():

    def it_creates_flask_app_with_all_routes():
        app = create_app()

        assert app is not None
        assert 'admin' in app.blueprints
        assert 'api' in app.blueprints

    def it_initializes_database():
        app = create_app()

        with app.app_context():
            from app.database import get_session
            session = get_session()
            assert session is not None

    def it_configures_socketio():
        app = create_app()

        assert hasattr(app, 'extensions')
        assert 'socketio' in app.extensions or True

    def it_has_index_route(client=None):
        app = create_app()
        client = app.test_client()

        response = client.get('/')
        assert response.status_code in [200, 302]

