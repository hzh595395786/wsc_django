from order.selectors import list_order_with_order_details_by_product_id


def list_order_with_order_details_by_product_id_interface(shop_id: int, product_id: int):
    """
    通过货品ID列出订单,带订单详情
    :param shop_id:
    :param product_id:
    :return:
    """
    order_list = list_order_with_order_details_by_product_id(shop_id, product_id)
    return order_list