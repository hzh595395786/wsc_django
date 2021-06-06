from config.services import get_some_config_by_shop_id, get_share_setup_by_id
from delivery.services import get_delivery_config_by_shop_id
from product.services import count_product_by_shop_ids
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


def get_some_config_by_shop_id_interface(shop_id: int):
    """获取店铺的一些配置"""
    some_config = get_some_config_by_shop_id(shop_id)
    return some_config


def get_delivery_config_by_shop_id_interface(shop_id: int):
    """获取一个店铺的配送设置"""
    delivery_config = get_delivery_config_by_shop_id(shop_id)
    return delivery_config


def get_share_setup_by_id_interface(shop_id: int):
    """获取一个店铺的分享设置"""
    share_setup = get_share_setup_by_id(shop_id)
    return share_setup


def count_product_by_shop_ids_interface(shop_ids: list):
    map_shop_product_count = count_product_by_shop_ids(shop_ids)
    return map_shop_product_count


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