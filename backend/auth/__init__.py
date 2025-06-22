"""
Authentication and authorization module
"""

from .auth_middleware import (
    get_current_user,
    require_workspace,
    require_permission,
    require_admin,
    require_write,
    require_read,
    AuthError
)

__all__ = [
    'get_current_user',
    'require_workspace',
    'require_permission',
    'require_admin',
    'require_write',
    'require_read',
    'AuthError'
]