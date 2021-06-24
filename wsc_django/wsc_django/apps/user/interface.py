from customer.models import Customer
from customer.services import get_customer_by_user_id_and_shop_id, get_customer_by_user_id_and_shop_code


def get_customer_by_user_id_and_shop_id_interface(user_id: int, shop_id: int) -> Customer:
    """
    通过user_id和shop_id获取客户
    :param user_id:
    :param shop_id:
    :return:
    """
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    return customer


def get_customer_by_user_id_and_shop_code_interface(user_id: int, shop_code: str) -> Customer:
    """
    通过user_id和shop_code获取客户
    :param user_id:
    :param shop_code:
    :return:
    """
    customer = get_customer_by_user_id_and_shop_code(user_id, shop_code)
    return customer