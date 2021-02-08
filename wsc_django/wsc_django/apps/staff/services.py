from shop.models import Shop
from user.models import User
from staff.models import Staff
from staff.constant import (
    StaffPermission,
    StaffRole,
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