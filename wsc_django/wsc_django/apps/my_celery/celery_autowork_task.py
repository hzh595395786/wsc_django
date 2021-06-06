""" 自动取消(订单，拼团)异步任务 """
import datetime
import os

# import sentry_sdk
from django.utils.timezone import make_aware
from celery import Celery
# from sentry_sdk.integrations.celery import CeleryIntegration

# from config.services import get_receipt_by_shop_id
from groupon.constant import GrouponStatus
from groupon.services import get_shop_groupon_by_id
from order.constant import OrderPayType, OrderRefundType, OrderType
from order.services import (
    cancel_order,
    # direct_pay,
    # refund_order,
    get_order_by_shop_id_and_id,
)
from promotion.events import GrouponEvent
from promotion.services import publish_product_promotion
from wsc_django.apps.settings import CELERY_BROKER
# from .celery_tplmsg_task import (
#     GrouponOrderFailAttendTplMsg,
#     GrouponOrderRefundFailTplMsg,
#     GrouponOrderSuccessAttendTplMsg,
# )

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.settings'

app = Celery("wsc_auto_work", broker=CELERY_BROKER, backend="")
app.conf.CELERY_TIMEZONE = "Asia/Shanghai"  # 时区
app.conf.CELERYD_CONCURRENCY = 4  # 任务并发数
app.conf.CELERYD_TASK_SOFT_TIME_LIMIT = 600  # 任务超时时间
app.conf.CELERY_DISABLE_RATE_LIMITS = True  # 任务频率限制开关
app.conf.CELERY_ROUTES = {
    "auto_cancel_order": {"queue": "wsc_auto_work"},
    "auto_publish_groupon": {"queue": "wsc_auto_work"},
    "auto_expire_groupon": {"queue": "wsc_auto_work"},
    # "auto_validate_groupon_attend": {"queue": "wsc_auto_work"},
    # "auto_fail_groupon_attend": {"queue": "wsc_auto_work"},
}

# sentry_sdk.init(SENTRY_DSN, integrations=[CeleryIntegration()])


@app.task(bind=True, name="auto_cancel_order")
def auto_cancel_order(self, shop_id, order_id):
    """ 超时未支付(15min)自动取消订单 """
    success, _ = cancel_order(shop_id, order_id)
    if success:
        return
    order = get_order_by_shop_id_and_id(shop_id, order_id)
    if not order:
        return
    # elif order.order_type == OrderType.GROUPON:
    #     auto_validate_groupon_attend.apply_async(
    #         args=[order.shop_id, order.groupon_attend_id]
    #     )


@app.task(bind=True, name="auto_publish_groupon")
def auto_publish_groupon(self, shop_id, groupon_id):
    """ 自动发布拼团事件 """
    now = make_aware(datetime.datetime.now())
    success, groupon = get_shop_groupon_by_id(shop_id, groupon_id)
    if not success:
        print("Groupon [id={}] publish failed: {}".format(groupon_id, groupon))
        return
    if groupon.status != GrouponStatus.ON:
        print(
            "Groupon [id={}] publish failed: 状态错误{}".format(
                groupon_id, groupon.status
            )
        )
        return
    if groupon.to_datetime < now:
        print(
            "Groupon [id={}] publish failed: 已过期{}".format(
                groupon_id, groupon.to_datetime
            )
        )
        return
    content = {
        "id": groupon.id,
        "price": round(float(groupon.price), 2),
        "to_datetime": groupon.to_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "groupon_type": groupon.groupon_type,
        "success_size": groupon.success_size,
        "quantity_limit": groupon.quantity_limit,
        "succeeded_count": groupon.succeeded_count,
        "success_limit": groupon.success_limit,
        "succeeded_quantity": int(round(groupon.succeeded_quantity)),
    }
    event = GrouponEvent(content)
    ttl = (groupon.to_datetime - now).total_seconds()
    publish_product_promotion(
        groupon.shop_id, groupon.product_id, event, ttl=int(ttl)
    )
    print("Groupon [id={}] publish success".format(groupon.id))


@app.task(bind=True, name="auto_expire_groupon")
def auto_expire_groupon(self, shop_id, groupon_id):
    """ 拼团自动过期 """
    success, groupon = get_shop_groupon_by_id(shop_id, groupon_id)
    if not success:
        print("Groupon [id={}] expire failed: {}".format(groupon_id, groupon))
        return
    if groupon.status == GrouponStatus.EXPIRED:
        print(
            "Groupon [id={}] expire failed: 状态错误{}".format(
                groupon_id, groupon.status
            )
        )
        return
    # 任务提前10s过期算作提前
    if groupon.to_datetime - make_aware(datetime.datetime.now()) > make_aware(datetime.timedelta(
        seconds=10
    )):
        print(
            "Groupon [id={}] expire failed: 未到过期时间{}".format(
                groupon_id, datetime.datetime.now()
            )
        )
        return
    groupon.set_expired()
    print("Groupon [id={}] expire failed".format(groupon_id))


# @app.task(bind=True, name="auto_validate_groupon_attend")
# def auto_validate_groupon_attend(
#     self, shop_id: int, groupon_attend_id: int, force: bool = False
# ):
#     """ 自动验证拼团参与，如果满员，走订单直接支付 """
#     session = scoped_DBSession()
#     try:
#         success, groupon_attend = get_shop_groupon_attend_by_id(
#             session, shop_id, groupon_attend_id, for_update=True
#         )
#         if not success:
#             raise ValueError(groupon_attend)
#         if groupon_attend.size < groupon_attend.success_size:
#             print("拼团验证: 拼团参与{}还未满员".format(groupon_attend_id))
#             return
#         if groupon_attend.status != GrouponAttendStatus.WAITTING:
#             raise ValueError(
#                 "拼团验证: 拼团参与{}状态错误{}".format(groupon_attend_id, groupon_attend.status)
#             )
#         paid_attend_lines = list_paid_lines_by_groupon_attend_id(
#             session, groupon_attend.id
#         )
#         if len(paid_attend_lines) < groupon_attend.size and not force:
#             print(
#                 "拼团验证: 拼团参与{}还在等待团员支付，当前支付人数{}".format(
#                     groupon_attend_id, len(paid_attend_lines)
#                 )
#             )
#             return
#         waitting_orders = list_waitting_orders_by_groupon_attend_id(
#             session, groupon_attend.id
#         )
#         if len(waitting_orders) != len(paid_attend_lines):
#             raise ValueError(
#                 "拼团验证: 拼团参与{}付款人数{}和订单人数{}不匹配".format(
#                     groupon_attend_id, len(paid_attend_lines), len(waitting_orders)
#                 )
#             )
#         promotion = get_product_promotion(shop_id, groupon_attend.groupon.product_id)
#         pattern = PRODUCT_PROMOTION_KEY.format(
#             shop_id=shop_id, product_id=groupon_attend.groupon.product_id
#         )
#         groupon_attend.set_succeeded()
#         groupon_attend.groupon.succeeded_count += 1
#         redis.hset(pattern, "succeeded_count", groupon_attend.groupon.succeeded_count)
#         for waitting_order in waitting_orders:
#             if promotion and isinstance(promotion, GrouponEvent):
#                 quantity = int(
#                     round(float(waitting_order.amount_net) / float(promotion.price))
#                 )
#                 groupon_attend.groupon.succeeded_quantity += quantity
#                 redis.hset(
#                     pattern,
#                     "succeeded_quantity",
#                     int(groupon_attend.groupon.succeeded_quantity),
#                 )
#             direct_pay(session, waitting_order)
#         print("拼团验证: 拼团参与{}成团成功".format(groupon_attend_id))
#         # 拼团成功, 发送拼团成功的模板消息
#         msg_notify = get_msg_notify_by_shop_id(session, shop_id)
#         if msg_notify.group_success_wx:
#             for waitting_order in waitting_orders:
#                 GrouponOrderSuccessAttendTplMsg.send(order_id=waitting_order.id)
#     finally:
#         session.close()


# @app.task(bind=True, name="auto_fail_groupon_attend")
# def auto_fail_groupon_attend(self, shop_id: int, groupon_attend_id: int, reason: str):
#     """ 拼团参与自动失败 """
#     session = scoped_DBSession()
#     try:
#         success, groupon_attend = get_shop_groupon_attend_by_id(
#             session, shop_id, groupon_attend_id, for_update=True
#         )
#         if not success:
#             raise ValueError(groupon_attend)
#         if groupon_attend.status != GrouponAttendStatus.WAITTING:
#             print("拼团失败: 拼团参与{}状态错误{}".format(groupon_attend_id, groupon_attend.status))
#             return
#         paid_attend_lines = list_paid_lines_by_groupon_attend_id(
#             session, groupon_attend.id
#         )
#         waitting_orders = list_waitting_orders_by_groupon_attend_id(
#             session, groupon_attend.id
#         )
#         if len(waitting_orders) != len(paid_attend_lines):
#             raise ValueError(
#                 "拼团失败: 拼团参与{}付款人数{}和订单人数{}不匹配".format(
#                     groupon_attend_id, len(paid_attend_lines), len(waitting_orders)
#                 )
#             )
#         groupon_attend.set_failed(reason)
#         # 拼团中订单自动退款
#         map_refund_order = {True: [], False: []}
#         for waitting_order in waitting_orders:
#             refund_type = (
#                 OrderRefundType.WEIXIN_JSAPI_REFUND
#                 if waitting_order.pay_type == OrderPayType.WEIXIN_JSAPI
#                 else OrderRefundType.UNDERLINE_REFUND
#             )
#             success, _ = refund_order(
#                 session, waitting_order.shop_id, waitting_order.id, refund_type
#             )
#             map_refund_order[success].append(waitting_order.id)
#         # 未支付订单自动取消
#         unpaid_orders = list_unpaid_orders_by_groupon_attend_id(
#             session, groupon_attend.id
#         )
#         for unpaid_order in unpaid_orders:
#             cancel_order(session, unpaid_order.shop_id, unpaid_order.id)
#         session.commit()
#         print(
#             "拼团失败: 拼团参与{},退款成功{},退款失败".format(
#                 groupon_attend_id,
#                 len(map_refund_order.get(True)),
#                 len(map_refund_order.get(False)),
#             )
#         )
#         # 拼团失败, 发送拼团失败退款的模板消息
#         msg_notify = get_msg_notify_by_shop_id(session, shop_id)
#         if msg_notify.group_failed_wx:
#             for order_id in map_refund_order.get(True):
#                 GrouponOrderFailAttendTplMsg.send(order_id=order_id)
#         for order_id in map_refund_order.get(False):
#             GrouponOrderRefundFailTplMsg.send(order_id=order_id)
#     finally:
#         session.close()
