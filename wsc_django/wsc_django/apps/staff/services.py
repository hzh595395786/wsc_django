from shop.models import Shop
from user.models import User
from staff.models import Staff, StaffApply
from staff.constant import (
    StaffPermission,
    StaffRole,
    StaffStatus,
    StaffApplyExpired,
)


def create_super_admin_staff(shop: Shop, user: User):
    """
    创建一个超级管理员
    :param shop:
    :param super_amdin:
    :return:
    """
    # 计算所有权限,超级管理员拥有所有权限
    permissions = 0
    for k, v in vars(StaffPermission).items():
        if not k.startswith("__"):
            permissions |= v

    staff = Staff.objects.create(
        shop=shop,
        user=user,
        roles=StaffRole.SHOP_SUPER_ADMIN,
        permissions=permissions
    )
    staff.save()
    return staff


def create_staff_apply(staff_apply_info: dict):
    """创建一条员工申请信息"""
    staff = StaffApply.objects.create(**staff_apply_info)
    staff.save()
    return staff


def get_staff_by_user_id_and_shop_id(user_id: int, shop_id: int, filter_delete: bool = True):
    """
    通过shop_id和user_id获取员工,不带user信息
    :param user_id:
    :param shop_id:
    :param filter_delete: 过滤删除
    :return:
    """
    staff_query = Staff.objects.filter(shop_id=shop_id, user_id=user_id)
    if staff_query and filter_delete:
        staff_query = staff_query.filter(status=StaffStatus.NORMAL)
    staff = staff_query.first()
    return staff


def get_staff_apply_by_user_id_and_shop_id(user_id: int, shop_id: int, filter_expired: bool = True):
    """
    通过店铺ID和用户ID获取一个人的最新员工申请记录
    :param shop_id:
    :param user_id:
    :param filter_expired: 过滤过期
    :return:
    """
    staff_apply_query = StaffApply.objects.filter(shop_id=shop_id, user_id=user_id)
    if staff_apply_query and filter_expired:
        staff_apply_query = staff_apply_query.filter(expired=StaffApplyExpired.NO)
    staff_apply = staff_apply_query.first()
    return staff_apply


def list_staff_by_user_id(user_id: int, roles: int = None, filter_delete: bool = True):
    """
    查询这个用户在所有店铺的员工信息
    :param user_id:
    :param roles:
    :param filter_delete: 过滤删除
    :return:
    """
    staff_list_query = Staff.objects.filter(user_id=user_id)
    if staff_list_query and filter_delete:
        staff_list_query = staff_list_query.filter(status=StaffStatus.NORMAL)
    if staff_list_query and roles:
        staff_list_query = staff_list_query.extra(where=['roles & 1'])
    staff_list = staff_list_query.all()
    return staff_list