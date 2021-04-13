from order.selectors import list_customer_orders


def list_customer_orders_interface(
    shop_id: int,
    customer_id: int,
    order_types: list,
    order_pay_types: list,
    order_delivery_methods: list,
    order_status: list,
):
    """
    获取一个客户的历史订单interface
    :param shop_id:
    :param customer_id:
    :param order_types:
    :param order_pay_types:
    :param order_delivery_methods:
    :param order_status:
    :return:
    """
    order_list = list_customer_orders(
        shop_id,
        customer_id,
        order_types,
        order_pay_types,
        order_delivery_methods,
        order_status,
    )
    return order_list