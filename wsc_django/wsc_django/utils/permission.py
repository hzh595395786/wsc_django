"""权限相关"""
from rest_framework.authentication import BaseAuthentication


class WSCStaffPermission(BaseAuthentication):
    """微商城员工权限验证"""

    def has_permission(self, request, view):

        return True