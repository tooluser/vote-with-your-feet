import pytest
from flask import Flask
from app.routes.admin import admin_bp
from app.config import Config


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['ADMIN_SECRET'] = 'test-secret'
    app.config['TESTING'] = True
    app.register_blueprint(admin_bp, url_prefix='/admin')
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def describe_admin_authentication():
    
    def it_requires_secret_query_parameter_or_header(client):
        response = client.get('/admin/test')
        assert response.status_code == 403
    
    def it_rejects_requests_without_valid_secret(client):
        response = client.get('/admin/test?secret=wrong-secret')
        assert response.status_code == 403
        
        response = client.get('/admin/test', headers={'X-Admin-Secret': 'wrong-secret'})
        assert response.status_code == 403
    
    def it_allows_access_with_valid_secret(client):
        response = client.get('/admin/test?secret=test-secret')
        assert response.status_code == 200
        assert b'Admin Test Route' in response.data
        
        response = client.get('/admin/test', headers={'X-Admin-Secret': 'test-secret'})
        assert response.status_code == 200
        assert b'Admin Test Route' in response.data

