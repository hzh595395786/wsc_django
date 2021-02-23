from staff.services import list_staff_by_user_id
from user.services import get_user_by_id
from customer.services import get_customer_by_user_id_and_shop_id


def get_user_by_id_interface(user_id: int) -> object:
    """获取一个用户"""
    user = get_user_by_id(user_id)
    return user


def get_customer_by_user_id_and_shop_id_interface(user_id: int, shop_id: int) -> object:
    """
    通过user_id和shop_id获取一个客户
    :param user_id:
    :return:
    """
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    return customer


def list_staff_by_user_id_interface(user_id: int, roles: int) -> list:
    """获取一个用户的所有员工信息"""
    staff_list = list_staff_by_user_id(user_id, roles)
    return staff_list