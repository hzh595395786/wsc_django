from groupon.services import list_alive_groupon_by_product_ids
from logs.services import create_product_log
from order.selectors import list_order_with_order_details_by_product_id


def list_order_with_order_details_by_product_id_interface(shop_id: int, product_id: int):
    """通过货品ID列出订单,带订单详情"""
    order_list = list_order_with_order_details_by_product_id(shop_id, product_id)
    return order_list


def list_alive_groupon_by_product_ids_interface(product_ids: list):
    """查询现在或者未来有拼团活动的商品ID"""
    product_ids_set = list_alive_groupon_by_product_ids(product_ids)
    return product_ids_set


def create_product_log_interface(log_info: dict):
    """创建一条货品模块日志"""
    log = create_product_log(log_info)
    return log