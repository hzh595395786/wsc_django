"""权限相关"""
from rest_framework.permissions import BasePermission
from rest_framework import exceptions


class StaffRolePermission(BasePermission):
    """员工角色权限验证"""

    def has_permission(self, request, view):
        if (
                view.current_staff.roles & view.staff_roles.SHOP_ADMIN == 0
                or view.current_staff.permissions == 0
        ):
            raise exceptions.PermissionDenied("该员工角色不满足")
        else:
            return True


class WSCStaffPermission(BasePermission):
    """员工权限验证"""

    def has_permission(self, request, view):
        if not view.current_shop or not view.current_staff:
            raise exceptions.PermissionDenied("店铺不存在或员工不存在")
        else:
            return True