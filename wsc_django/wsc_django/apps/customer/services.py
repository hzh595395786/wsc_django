from customer.models import Customer
from user.constant import USER_OUTPUT_CONSTANT
from user.services import get_user_by_id


def create_customer(user_id: int, shop_id: int):
    """
    创建客户
    :param user_id:
    :param shop_id:
    :return:
    """
    customer = Customer.objects.create(shop_id=shop_id, user_id=user_id)
    customer.save()
    return customer


def get_customer_by_user_id_and_shop_id(user_id: int, shop_id: int):
    """
    通过店铺ID和userID查到一个客户
    :param user_id:
    :return:
    """
    customer = Customer.objects.filter(user_id=user_id, shop_id=shop_id).first()
    return customer


def get_customer_by_customer_id_and_shop_id(
        customer_id: int,
        shop_id: int,
        with_user_info: bool=False
):
    """
    通过客户id和商铺id查询单个客户信息,包括详情
    :param customer_id:
    :param shop_id:
    :param with_user_info: 带上用户信息
    :return:
    """
    customer = Customer.objects.filter(shop_id=shop_id, id=customer_id).first()
    if customer and with_user_info:
        # 查询用户信息
        user = get_user_by_id(customer.user_id)
        customer_personal_data = {key: getattr(user, key)for key in USER_OUTPUT_CONSTANT}
        customer.customer_personal_data = customer_personal_data
    return customer