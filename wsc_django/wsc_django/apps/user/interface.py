from customer.services import get_customer_by_user_id_and_shop_id


def get_customer_by_user_id_and_shop_id_interface(user_id: int, shop_id: int) -> object:
    """
    通过user_id获取客户
    :param user_id:
    :param shop_id:
    :return:
    """
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    return customer