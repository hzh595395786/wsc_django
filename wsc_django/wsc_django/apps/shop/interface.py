from staff.services import list_staff_by_user_id
from user.services import get_user_by_id, list_user_by_ids
from customer.services import get_customer_by_user_id_and_shop_id


def get_user_by_id_interface(user_id: int) -> object:
    """
    获取一个用户
    :param user_id:
    :return:
    """
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
    """
    获取一个用户的所有员工信息
    :param user_id:
    :param roles:
    :return:
    """
    staff_list = list_staff_by_user_id(user_id, roles)
    return staff_list


def list_user_by_ids_interface(user_ids: list) -> list:
    """
    通过user_ids列出用户
    :param user_ids:
    :return:
    """
    user_list = list_user_by_ids(user_ids)
    return user_list