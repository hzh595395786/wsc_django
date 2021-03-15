from logs.services import get_order_log_time_by_order_num
from order.constant import OrderStatus
from order.models import Order, OrderAddress, OrderDetail
from user.constant import USER_OUTPUT_CONSTANT


def get_order_by_shop_id_and_id(shop_id: int, order_id: int):
    """
    通过商铺ID和订单ID获取订单
    :param shop_id:
    :param order_id:
    :return:
    """
    order = Order.objects.filter(id=order_id, shop_id=shop_id).first()
    return order


def get_shop_order_by_shop_id_and_id(shop_id: int, order_id: int):
    """
    通过商铺id和订单id获取订单及详情
    :param shop_id:
    :param order_id:
    :return:
    """
    order = Order.objects.filter(shop_id=shop_id, id=order_id).first()
    if not order:
        return False, "订单不存在"
    order.order_detail = list_order_details_by_order_id([order.id])
    order_address = get_order_address_by_order_id(order.id)
    if order_address:
        order.address = order_address
    return True, order


def get_order_address_by_order_id(order_id: int):
    """
    通过订单id获取订单地址
    :param order_id:
    :return:
    """
    order_address = OrderAddress.objects.filter(order_id=order_id).first()
    return order_address


def list_order_details_by_order_ids(order_ids: list):
    """
    通过订单id列表获取订单详情
    :param order_ids:
    :return:
    """
    order_details = OrderDetail.objects.filter(order_id__in=order_ids).all()
    for order_detail in order_details:
        order_detail.product_name = order_detail.product.name
        order_detail.product_id = order_detail.product.id
        order_detail.product_cover_picture = order_detail.product.cover_image_url
    return order_details


def list_order_with_order_details_by_product_id(shop_id: int, product_id: int):
    """
    通过货品ID查询出其对应的销售记录(订单记录)
    :param shop_id:
    :param product_id:
    :return:
    """
    order_with_order_details_query = Order.objects.filter(
        shop_id=shop_id, order_detail__product_id=product_id
    ).order_by("id")
    order_with_order_details = order_with_order_details_query.all()
    for order in order_with_order_details:
        for od in order.order_detail.all():
            if not od.product_id == product_id:
                continue
            else:
                order_detail = od
        order.price_net = order_detail.price_net
        order.quantity_net = order_detail.quantity_net
        order.amount_net = order_detail.amount_net
        order.customer_data = order.customer.user
    return order_with_order_details


def get_order_by_num_for_update(num: str):
    """
    通过订单获取订单-加锁
    :param num:
    :return:
    """
    result = Order.objects.select_for_update().filter(num=num).first()
    return result


def list_order_details_by_order_id(order_id: int):
    """
    通过订单ID获取子订单列表
    :param order_id:
    :return:
    """
    order_detail_list = OrderDetail.objects.filter(order_id=order_id).all()
    return order_detail_list


def get_order_detail_by_id_only_msg_notify(order_id: int):
    """
    通过订单ID获取订单及详情，专供订单微信消息通知使用，其他地方不要调用
    :param order_id:
    :return:
    """
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return False, "订单不存在"
    order.order_details = list_order_details_by_order_ids([order.id])
    order.address = get_order_address_by_order_id(order.id)
    return True, order


def get_customer_order_by_id(customer_ids: list, order_id: int):
    """
    通过客户ids和订单id查找一个客户的订单
    :param customer_ids:
    :param order_id:
    :return:
    """
    order = Order.objects.filter(customer_id__in=customer_ids, id=order_id).first()
    return order


def get_customer_order_with_detail_by_id(customer_ids: list, order_id: int):
    """
    通过客户ids和订单id查找一个客户的订单详情
    :param customer_ids:
    :param order_id:
    :return:
    """
    order = get_customer_order_by_id(customer_ids, order_id)
    if not order:
        return False, "订单不存在"
    # 查找订单地址与订单商品详情
    order.order_details = list_order_details_by_order_ids([order.id])
    order.address = get_order_address_by_order_id(order.id)
    # 查找配送记录
    if order.order_status in [OrderStatus.CONFIRMED, OrderStatus.FINISHED]:
        # 查找最新的操作时间,作为订单开始或送达时间
        order.delivery_time = get_order_log_time_by_order_num(order.order_num)
    return True, order
