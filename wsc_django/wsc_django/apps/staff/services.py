from django.db.models import Q

from shop.models import Shop
from user.models import User
from staff.models import Staff, StaffApply
from staff.constant import (
    StaffPermission,
    StaffRole,
    StaffStatus,
    StaffApplyExpired,
)


def cal_all_permission():
    """计算所有的权限"""
    permissions = 0
    for k, v in vars(StaffPermission).items():
        if not k.startswith("_"):
            permissions |= v
    return permissions


def cal_all_roles_without_super():
    """计算所有的角色,除超管"""
    roles = 0
    for k, v in vars(StaffRole).items():
        if not k.startswith("_") and v != StaffRole.SHOP_SUPER_ADMIN:
            roles |= v
    return roles


def create_staff(staff_info: dict):
    """

    :param staff_info: {
        "shop_id": 1,
        "user_id": 1,
        "roles": 255,
        "permissions": 63,
        "position": "",
        "entry_date": "2019-10-14",
        "remark": ""
    }
    :return:
    """
    staff = Staff.objects.create(**staff_info)
    staff.save()
    return staff


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


def expire_staff_apply_by_staff(shop_id: int, user_id: int):
    """
    删除员工时使其申请记录过期
    :param shop_id:
    :param user_id:
    :return:
    """
    staff_apply_list = list_staff_apply_by_shop_id_and_user_id(shop_id, user_id, filter_expired=True)
    for sal in staff_apply_list:
        sal.expired = StaffApplyExpired.YES
        sal.save()


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


def get_staff_apply_by_shop_id_and_id(
        shop_id: int, staff_apply_id: int, filter_expired: bool = True
):
    """
    通过shop_id和id获取一个申请记录, 未过期只会有一条
    :param shop_id:
    :param staff_apply_id:
    :param filter_expired: 过滤过期
    :return:
    """
    staff_apply_query = StaffApply.objects.filter(shop_id=shop_id, id=staff_apply_id)
    if filter_expired:
        staff_apply_query = staff_apply_query.filter(expired=StaffApplyExpired.NO)
    staff_apply = staff_apply_query.first()
    return staff_apply


def get_staff_by_id_and_shop_id(
        staff_id: int, shop_id: int, filter_delete: bool = True
):
    """
    通过staff_id和shop_id查询一个员工
    :param staff_id:
    :param shop_id:
    :param filter_delete: 过滤删除
    :return:
    """
    staff_query = Staff.objects.filter(id=staff_id, shop_id=shop_id)
    if filter_delete:
        staff_query = staff_query.filter(status=StaffStatus.NORMAL)
    staff = staff_query.first()
    return staff


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


def list_staff_apply_by_shop_id(shop_id: int):
    """
    查询一个店铺的员工申请记录
    :param shop_id:
    :return:
    """
    staff_apply_list = StaffApply.objects.filter(shop_id=shop_id).order_by('id').all()
    return staff_apply_list


def list_staff_apply_by_shop_id_and_user_id(
    shop_id: int, user_id: int, filter_expired: bool = False
):
    """
    查询一个人在一个店铺的所有的申请记录-未过期的理论只会有一条
    :param shop_id:
    :param user_id:
    :param filter_expired: 过滤过期
    :return:
    """
    staff_apply_query = StaffApply.objects.filter(shop_id=shop_id, user_id=user_id)
    if filter_expired:
        staff_apply_query = staff_apply_query.filter(expired=StaffApplyExpired.NO)
    staff_apply = staff_apply_query.all()
    return staff_apply


def list_staff_by_shop_id(shop_id: int, keyword: str = None):
    """
    查询一个店铺的所有员工信息, 过滤已删除员工
    :param shop_id:
    :param keyword: 过滤关键词
    :return:
    """
    if keyword:
        staff_list_query = (
            Staff.objects.filter(shop_id=shop_id, status=StaffStatus.NORMAL)
            .filter(
                Q(user__realname__contains=keyword) |
                Q(user__nickname__contains=keyword) |
                Q(user__phone__contains=keyword)
            )
        )
    else:
        staff_list_query = Staff.objects.filter(shop_id=shop_id, status=StaffStatus.NORMAL)
    staff_list = staff_list_query.all()
    return staff_list