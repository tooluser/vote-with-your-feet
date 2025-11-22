from flask import Blueprint
from app.middleware.auth import require_admin_secret

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/test')
@require_admin_secret
def test_route():
    """Test route to verify authentication"""
    return 'Admin Test Route', 200

