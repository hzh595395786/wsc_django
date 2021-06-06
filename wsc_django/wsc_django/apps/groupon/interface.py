import datetime

from django.utils.timezone import make_aware

from groupon.models import Groupon, GrouponAttend
from celery_tasks.celery_auto_work.tasks import (
    auto_publish_groupon,
    auto_expire_groupon,
    auto_fail_groupon_attend,
    auto_cancel_order,
    auto_validate_groupon_attend)

from order.selectors import list_unpay_order_by_groupon_attend_ids, list_order_by_groupon_attend_id


def publish_gruopon_interface(groupon: Groupon):
    """
    根据拼团开始时间发布拼团
    :param groupon:
    :return:
    """
    countdown = (groupon.from_datetime - make_aware(datetime.datetime.now())).total_seconds()
    # 当前时间以前的拼团直接发布，当前时间以后的拼团直接发布
    auto_publish_groupon.apply_async(
        args=(groupon.shop.id, groupon.id),
        countdown=int(countdown) if countdown > 0 else 0,
    )


def expire_groupon_interface(groupon: Groupon):
    """
    根据拼团结束时间过期拼团
    :param groupon:
    :return:
    """
    countdown = (groupon.to_datetime - make_aware(datetime.datetime.now())).total_seconds()
    auto_expire_groupon.apply_async(
        args=(groupon.shop.id, groupon.id),
        countdown=int(countdown) if countdown > 0 else 0,
    )


def immediate_fail_groupon_attend_interface(shop_id: int, groupon_attend: GrouponAttend):
    """立即失效拼团参与(拼团停用)"""
    reason = "商家停用该活动"
    auto_fail_groupon_attend.apply_async(args=[shop_id, groupon_attend.id, reason])


def list_unpay_order_by_groupon_attend_ids_interface(groupon_attend_ids: list):
    """通过拼团参与id列表列出没支付的订单"""
    orders = list_unpay_order_by_groupon_attend_ids(groupon_attend_ids)
    return orders


def immediate_cancel_order_interface(shop_id: int, order_id: int):
    """立即取消订单"""
    auto_cancel_order.apply_async(args=[shop_id, order_id])


def list_order_by_groupon_attend_id_interface(shop_id: int, groupon_attend_id: int):
    """通过拼团参与ID列出一个团的订单"""
    order_list = list_order_by_groupon_attend_id(shop_id, groupon_attend_id)
    return order_list


def sync_success_groupon_attend_interface(shop_id: int, groupon_attend_id: int):
    """同步强制成团"""
    auto_validate_groupon_attend.apply_async(
        args=[shop_id, groupon_attend_id],
        kwargs={"force": True}
    )


def delay_fail_groupon_attend_interface(shop_id: int, groupon_attend: GrouponAttend):
    """延迟失效拼团参与(拼团参与自动过期)"""
    countdown = (groupon_attend.to_datetime - make_aware(datetime.datetime.now())).total_seconds()
    reason = "超过开团有效时间"
    auto_fail_groupon_attend.apply_async(
        args=[shop_id, groupon_attend.id, reason],
        countdown=int(countdown) if countdown > 0 else 0,
    )