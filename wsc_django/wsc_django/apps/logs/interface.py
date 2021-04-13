from staff.services import list_staff_by_shop_id_with_user


def list_operator_by_shop_id_with_user_interface(shop_id: int):
    """查询出一个店铺所有员工的user信息"""
    operator_list = list_staff_by_shop_id_with_user(shop_id)
    return operator_list