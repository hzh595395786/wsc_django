from config.services import get_msg_notify_by_shop_id
from customer.services import list_customer_ids_by_user_id, get_customer_by_user_id_and_shop_id
from delivery.services import get_order_delivery_by_delivery_id, create_order_delivery
from groupon.models import GrouponAttend
from groupon.services import get_groupon_by_id, count_groupon_attend_by_groupon_id_and_customer_id
from order.models import Order
from celery_tasks.celery_auto_work.tasks import auto_cancel_order, auto_validate_groupon_attend
from payment.service import get_wx_jsApi_pay
from printer.services import print_order
from product.services import list_product_by_ids, get_product_by_id
from logs.services import list_order_log_by_shop_id_and_order_num
# from celery_task.celery_tplmsg_task import (
#     OrderCommitTplMsg,
#     OrderDeliveryTplMsg,
#     OrderFinishTplMsg,
#     OrderRefundTplMsg,
# )
from promotion.services import get_product_promotion


def list_product_by_ids_interface(shop_id: int, product_ids: list) -> list:
    """通过ID列出商品"""
    product_list = list_product_by_ids(shop_id, product_ids)

    return product_list


def get_product_by_id_interface(shop_id: int, product_id: int) -> object:
    """通过店铺ID与货品ID获取一个货品"""
    product = get_product_by_id(shop_id, product_id)

    return product


def jsapi_params_interface(order, wx_openid):
    """公众号支付参数获取"""
    return get_wx_jsApi_pay(order, wx_openid)


def auto_cancel_order_interface(shop_id, order_id):
    """超时未支付(15min)自动取消订单"""
    auto_cancel_order.apply_async(args=(shop_id, order_id), countdown=15 * 60)


def order_commit_tplmsg_interface(order_id: int) -> None:
    """发送订单提交成功模板消息"""
    # OrderCommitTplMsg.send(order_id=order_id)


def list_customer_ids_by_user_id_interface(user_id: int) -> list:
    """通过user_id获取一个人所有的客户信息"""
    customer_ids = list_customer_ids_by_user_id(user_id)
    return customer_ids


def get_customer_by_user_id_and_shop_id_interface(user_id: int, shop_id: int):
    """通过user_id和shop_id获取一个客户"""
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    return customer


def list_order_log_by_shop_id_and_order_num_interface(shop_id: int, order_num: str):
    """获取一个订单的历史操作记录"""
    log_list = list_order_log_by_shop_id_and_order_num(shop_id, order_num)
    return log_list


def get_order_delivery_by_delivery_id_interface(delivery_id: int):
    """获取订单配送记录"""
    order_delivery = get_order_delivery_by_delivery_id(delivery_id)
    return order_delivery


def print_order_interface(order: Order, user_id: int):
    """订单打印"""
    return print_order(order, user_id)


def create_order_delivery_interface(delivery_info: dict):
    """创建订单配送记录"""
    delivery = create_order_delivery(delivery_info)
    return delivery


def get_msg_notify_by_shop_id_interface(shop_id: int):
    """获取一个店铺的消息通知设置"""
    msg_notify = get_msg_notify_by_shop_id(shop_id)
    return msg_notify


def auto_validate_groupon_attend_interface(shop_id: int, groupon_attend: GrouponAttend):
    """自动验证拼团参与，如果满员，走订单直接支付"""
    if not groupon_attend:
        return
    auto_validate_groupon_attend.apply_async(args=[shop_id, groupon_attend.id])


def get_product_promotion_interface(shop_id: int, product_id: int):
    """获取一个商品的活动"""
    event = get_product_promotion(shop_id, product_id)
    return event


def get_groupon_by_id_interface(shop_id: int, groupon_id: int):
    """获取一个拼团"""
    groupon = get_groupon_by_id(shop_id, groupon_id)
    return groupon


def count_groupon_attend_by_groupon_id_and_customer_id_interface(
    groupon_id: int, customer_id: int
):
    """
    计算一个人在某个拼团的参与次数
    :param groupon_id:
    :param customer_id:
    :return:
    """
    total_attend_count = count_groupon_attend_by_groupon_id_and_customer_id(
        groupon_id, customer_id
    )
    return total_attend_count


def order_delivery_tplmsg_interface(order_id: int):
    """发送订单配送模板消息"""
    # OrderDeliveryTplMsg.send(order_id=order_id)


def order_finish_tplmsg_interface(order_id: int):
    """发送订单完成模板消息"""
    # OrderFinishTplMsg.send(order_id=order_id)


def order_refund_tplmsg_interface(order_id: int):
    """发送订单退款模板消息"""
    # OrderRefundTplMsg.send(order_id=order_id)