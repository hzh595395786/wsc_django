"""权限相关"""
from rest_framework.permissions import BasePermission


class WSCAdminPermission(BasePermission):
    """微商城后台权限验证"""

    def has_permission(self, request, view):
        if (
                view.current_staff.roles & view.staff_roles.SHOP_ADMIN == 0
            or view.current_staff.permissions == 0
        ):
            return False
        return True