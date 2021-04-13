from collections import defaultdict

from logs.services import get_order_log_time_by_order_num
from order.constant import OrderStatus
from order.models import Order, OrderAddress, OrderDetail
from user.constant import USER_OUTPUT_CONSTANT


def get_shop_order_by_num(shop_id: int, num: str):
    """
    通过店铺id和订单号获取订单及详情
    :param shop_id:
    :param num:
    :return:
    """
    order = Order.objects.filter(shop_id=shop_id, order_num=num).first()
    if not order:
        return False, "订单不存在"
    order.order_details = list_order_details_by_order_ids([order.id])
    order_address = get_order_address_by_order_id(order.id)
    if order_address:
        order.address = order_address
    # 设置顾客信息
    for key in USER_OUTPUT_CONSTANT:
        setattr(order.customer, key, getattr(order.customer.user, key))
    return True, order


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


def get_shop_order_by_num_without_details(shop_id: int, order_num: int):
    """
    通过订单号获取一个订单
    :param shop_id:
    :param order_num:
    :return:
    """
    order = Order.objects.filter(shop_id=shop_id, order_num=order_num).first()
    return order


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
        for key in USER_OUTPUT_CONSTANT:
            setattr(order.customer, key, getattr(order.customer.user, key))
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


def list_shop_abnormal_orders(
    shop_id: int,
    order_types: list,
    order_pay_types: list,
    order_delivery_methods: list,
    order_status: list,
    num: str = None,
):
    """
    获取商铺的异常订单列表
    :param shop_id:
    :param order_types:
    :param order_pay_types:
    :param order_delivery_methods:
    :param order_status:
    :param num:
    :return:
    """
    # 获取异常订单列表
    if num:
        orders = (
            Order.objects.filter(
                shop_id=shop_id, order_num=num, order_status=OrderStatus.REFUND_FAIL
            )
        )
    else:
        orders = (
            Order.objects.filter(
                order_type__in=order_types,
                pay_type__in=order_pay_types,
                delivery_method__in=order_delivery_methods,
                order_status__in=order_status,
            )
        )
    order_list = orders.order_by("delivery_method", "delivery_period", "-id").all()
    # 订单详情
    order_ids = [order.id for order in order_list]
    order_details = list_order_details_by_order_ids(order_ids)
    map_order_lines = defaultdict(list)
    for order_detail in order_details:
        map_order_lines[order_detail.order_id].append(order_detail)
    # 拼数据
    for order in order_list:
        order.order_details = map_order_lines.get(order.id)
    return order_list



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


def list_shop_orders(
    shop_id: int,
    order_types: list,
    order_pay_types: list,
    order_delivery_methods: list,
    order_status: list,
    num: str = None,
):
    """
    获取店铺订单列表
    :param shop_id:
    :param order_types:
    :param order_pay_types:
    :param order_delivery_methods:
    :param order_status:
    :param num:
    :return:
    """
    if num:
        order_list = (
            Order.objects.filter(shop_id=shop_id, order_num=num)
            .filter(
                order_status__in=[
                    OrderStatus.PAID,
                    OrderStatus.CONFIRMED,
                    OrderStatus.FINISHED,
                    OrderStatus.REFUNDED,
                ]
            )
            .all()
        )
    else:
        order_list =(
            Order.objects.filter(shop_id=shop_id)
            .filter(
                order_type__in=order_types,
                pay_type__in=order_pay_types,
                delivery_method__in=order_delivery_methods,
                order_status__in=order_status
            )
            .order_by(
                "order_status", "delivery_method", "delivery_period", "-id"
            )
            .all()
        )

    # 订单详情
    order_ids = [order.id for order in order_list]
    order_details = list_order_details_by_order_ids(order_ids)
    map_order_lines = defaultdict(list)
    for order_detail in order_details:
        map_order_lines[order_detail.order_id].append(order_detail)
    # 拼数据
    for order in order_list:
        order.order_details = map_order_lines.get(order.id)
        # 拼装顾客数据
        for _ in USER_OUTPUT_CONSTANT:
            setattr(order.customer, _ , getattr(order.customer.user, _))
    return order_list


def list_customer_orders(
    shop_id: int,
    customer_id: int,
    order_types: list,
    order_pay_types: list,
    order_delivery_methods: list,
    order_status: list,
):
    """
    获取一个客户的历史订单列表
    :param shop_id:
    :param customer_id:
    :param order_types:
    :param order_pay_types:
    :param order_delivery_methods:
    :param order_status:
    :return:
    """
    order_list_query = Order.objects.filter(shop_id=shop_id, customer_id=customer_id)
    if order_types:
        order_list_query = order_list_query.filter(order_types__in=order_types)
    if order_pay_types:
        order_list_query = order_list_query.filter(order_pay_types__in=order_pay_types)
    if order_delivery_methods:
        order_list_query = order_list_query.filter(delivery_method__in=order_delivery_methods)
    if order_status:
        order_list_query = order_list_query.filter(order_status__in=order_status)
    order_list = order_list_query.order_by(
        "order_status", "delivery_method", "delivery_period", "-id"
    ).all()
    # 订单详情
    order_ids = [order.id for order in order_list]
    order_details = list_order_details_by_order_ids(order_ids)
    map_order_lines = defaultdict(list)
    for order_detail in order_details:
        map_order_lines[order_detail.order_id].append(order_detail)
    # 拼数据
    for order in order_list:
        order.order_details = map_order_lines.get(order.id)
    return order_list


def list_customer_order_by_customer_ids(customer_ids: list):
    """
    通过用户ID查出一个用户(对应多个客户)的所有订单
    :param customer_ids:
    :return:
    """
    order_list_query = (
        Order.objects.filter(customer_id__in=customer_ids)
        .order_by("-create_time")
    )
    order_list = order_list_query.all()
    # 订单详情
    order_ids = [order.id for order in order_list]
    order_details = list_order_details_by_order_ids(order_ids)
    map_order_lines = defaultdict(list)
    for order_detail in order_details:
        map_order_lines[order_detail.order_id].append(order_detail)
    # 拼数据
    for order in order_list:
        order.order_details = map_order_lines.get(order.id)
        if order.delivery:
            order.delivery_type = order.delivery.delivery_type
    return order_list


def count_abnormal_order(shop_id: int):
    """
    获取一个店铺异常(退款失败)的订单数
    :param shop_id:
    :return:
    """
    count = (
        Order.objects.filter(
            shop_id=shop_id,
            order_status=OrderStatus.REFUND_FAIL,
        )
        .count()
    )
    return count