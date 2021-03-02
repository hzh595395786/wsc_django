from order.models import Order


def list_order_with_order_lines_by_product_id(shop_id: int, product_id: int):
    """
    通过货品ID查询出其对应的销售记录(订单记录)
    :param shop_id:
    :param product_id:
    :return:
    """
    # todo 待写
    order_with_order_lines_query = Order
    return