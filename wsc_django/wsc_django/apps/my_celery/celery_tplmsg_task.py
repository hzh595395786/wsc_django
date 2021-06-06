""" 微信模板消息异步任务 """
import copy
import sys
import urllib.parse

from celery import Celery
from django_redis import get_redis_connection
from wechatpy.client import WeChatClient

from user.services import list_openid_by_user_ids_and_appid
from order.selectors import get_order_detail_by_id_only_msg_notify
from wsc_django.utils.constant import DateFormat
from delivery.constant import DeliveryType
from order.constant import OrderDeliveryMethod, OrderType
from wsc_django.apps.settings import CELERY_BROKER, MP_APPID, MP_APPSECRET, WSC_HOST_NAME


debug = False
if "-n123" in sys.argv:
    debug = True

app = Celery("wsc_tpl_msg", broker=CELERY_BROKER, backend="")
app.conf.timezone = "Asia/Shanghai"  # 时区
app.conf.worker_concurrency = 4  # 任务并发数
app.conf.task_soft_time_limit = 300  # 任务超时时间
app.conf.worker_disable_rate_limits = True  # 任务频率限制开关
app.conf.task_routes = {}  # 任务调度队列, 在register_celery里面自动注册

# 颜色常量
COLOR_GREEN = "#44b549"
COLOR_RED = "#FF0000"
COLOR_BLUE = "#173177"
COLOR_BLACK = "#333"

# 模板类型
ORDER_COMMIT = 1  # 提交订单
ORDER_DELIVERY = 2  # 订单配送
ORDER_FINISH = 3  # 订单完成
ORDER_REFUND = 4  # 订单退款
REFUND_FAIL = 5  # 拼团自动退款失败


# 模板
TEMPLATES = {
    ORDER_COMMIT: {
        "first": {"value": "{}", "color": COLOR_GREEN},
        "keyword1": {"value": "{}", "color": COLOR_BLACK},
        "keyword2": {"value": "{}", "color": COLOR_BLACK},
        "keyword3": {"value": "{}", "color": COLOR_BLACK},
        "keyword4": {"value": "{}", "color": COLOR_BLACK},
        "remark": {"value": "{}", "color": COLOR_BLUE},
    },
    ORDER_DELIVERY: {
        "first": {"value": "{}", "color": COLOR_GREEN},
        "keyword1": {"value": "{}", "color": COLOR_BLACK},
        "keyword2": {"value": "{}", "color": COLOR_BLACK},
        "keyword3": {"value": "{}", "color": COLOR_BLACK},
        "keyword4": {"value": "{}", "color": COLOR_BLACK},
        "remark": {"value": "{}", "color": COLOR_BLUE},
    },
    ORDER_FINISH: {
        "first": {"value": "{}", "color": COLOR_GREEN},
        "keyword1": {"value": "{}", "color": COLOR_BLACK},
        "keyword2": {"value": "{}", "color": COLOR_BLACK},
        "remark": {"value": "{}", "color": COLOR_BLUE},
    },
    ORDER_REFUND: {
        "first": {"value": "{}", "color": COLOR_GREEN},
        "keyword1": {"value": "{}", "color": COLOR_BLACK},
        "keyword2": {"value": "{}", "color": COLOR_BLACK},
        "keyword3": {"value": "{}", "color": COLOR_BLACK},
        "keyword4": {"value": "{}", "color": COLOR_BLACK},
    },
    REFUND_FAIL: {
        "first": {"value": "{}", "color": COLOR_GREEN},
        "keyword1": {"value": "{}", "color": COLOR_BLACK},
        "keyword2": {"value": "{}", "color": COLOR_BLACK},
        "keyword3": {"value": "{}", "color": COLOR_BLACK},
        "keyword4": {"value": "{}", "color": COLOR_BLACK},
        "remark": {"value": "{}", "color": COLOR_BLUE},
    },
}


def register_celery():
    def register(cls):
        cls_name = cls.__name__
        celery_func_name = "celery_send_{}".format(cls_name)
        celery_name = "tpl_msg.send{}".format(cls_name)
        celery_func = app.task(bind=True, name=celery_name)(cls._run)
        setattr(cls, celery_func_name, celery_func)
        app.conf.task_routes[celery_name] = {"queue": "wsc_tpl_msg"}

        return cls

    return register


class TplMsgStrategy:
    """ 策略基类，不提供数据，仅仅提供一个格式化成微信参数的方法
    :param tpl_format: int, 模板的格式类型
    :param default_template_id: string, 默认的模板id，通过森果公众号发送的模板
    :param template_id_short: string, 短模板id主要用于获取第三方公众号的模板id
    :param special_color: dict, 特殊的颜色控制
    """

    _tpl_format = None
    _default_template_id = None
    _template_id_short = None
    _special_color = None

    @classmethod
    def _format(cls, **kwargs):
        """ 格式化各个策略生成的参数，生成微信可以识别的字典

        :params *args: 可变参数, 这个可变参数主要定义了策略子类中get()方法需要的所有参数
        :params **kwargs: 可变关键字参数
        """
        tpl = cls._get_tpl()
        url, data = cls._get(**kwargs)
        for k, v in data.items():
            tpl[k]["value"] = v
        if cls._special_color:
            tpl = cls._change_color(cls._special_color, tpl)

        return url, tpl

    @classmethod
    def _get_tpl(cls):
        """ 根据各个策略的配置(tpl_format)从模板库中获取模板的格式, 并重新生成一份

        :rtype: dict, 传给微信的字典
        """
        tpl = copy.deepcopy(TEMPLATES.get(cls._tpl_format))
        if not tpl:
            raise NotImplementedError
        return tpl

    @classmethod
    def _get(cls, **kwargs):
        """ 提供访问url和data
        :param order: 订单对象,包含各种详情
        :return: url, string, 微信模板消息对应的链接地址
        :return: data, dict, 发送给微信的详细参数
        :rtype: tuple, (url, data)
        """
        raise NotImplementedError

    @classmethod
    def _change_color(self, color, tpl):
        """ 在模板样式基础上做的字体颜色调整

        :param color: dict, 要改变颜色的键的字典
        :param tpl: dict, 模板字典
        """
        for k, v in color.items():
            tpl[k]["color"] = v
        return tpl

    @classmethod
    def send(cls, **kwargs):
        """必传参数order_id"""
        cls_name = cls.__name__
        handler_method = getattr(cls, "celery_send_{}".format(cls_name))
        handler_method.delay(cls_name, **kwargs)

    def _run(self, cls_name, **kwargs):
        """self是_run函数本身"""
        cls = eval(cls_name)
        to_user_id_list, shop_id, new_kwargs = cls._middle_handler(
            **kwargs
        )
        touser_list, template_id, wechat_client = cls._get_mp_info(
            to_user_id_list, shop_id
        )
        url, tpl = cls._format(**new_kwargs)
        for touser in touser_list:
            try:
                ret = wechat_client.message.send_template(
                    user_id=touser, template_id=template_id, data=tpl, url=url
                )
                print(ret)
            except Exception as e:
                print(str(e))

    @classmethod
    def _middle_handler(cls, **kwargs):
        """获取发送人"""
        raise NotImplementedError

    @classmethod
    def _get_mp_info(cls, to_user_id_list, shop_id):
        """获取发送人的微信openid与微信对象"""
        app_id = MP_APPID
        app_secret = MP_APPSECRET
        template_id = cls._default_template_id
        # 森果自己的微信公众号和零售共用一个
        redis_conn = get_redis_connection("default")
        access_token = redis_conn.get("access_token")
        access_token = access_token.decode("utf-8") if access_token else None
        wechat_client = WeChatClient(
            appid=app_id, secret=app_secret, access_token=access_token, timeout=5
        )
        if not access_token:
            access_token = wechat_client.fetch_access_token()
            redis_conn.setex("access_token", 3600, access_token.get("access_token"))

        user_openid_list = list_openid_by_user_ids_and_appid(
            to_user_id_list, app_id
        )
        touser_list = [user_openid.wx_openid for user_openid in user_openid_list]

        return touser_list, template_id, wechat_client


# 普通订单提交成功通知
@register_celery()
class OrderCommitTplMsg(TplMsgStrategy):
    """订单提交成功消息模板通知"""

    _tpl_format = ORDER_COMMIT
    _default_template_id = (
        "4QuRCzRuxVFWuz1gw8hHXlAaJZL4H2lLAyPXNr1MXIs"
        if not debug
        else "j33gYWAno6Q0_tqzWI40ZoAj3m39TEp-seWH_biCdBs"
    )
    _template_id_short = "OPENTM410958953"

    @classmethod
    def _middle_handler(cls, **kwargs):
        order_id = kwargs["order_id"]
        res, order = get_order_detail_by_id_only_msg_notify(order_id)
        if not res:
            raise ValueError("订单不存在")
        to_user_id_list = [order.customer.user.id]
        shop_id = order.shop.id
        new_kwargs = {"order": order}

        return to_user_id_list, shop_id, new_kwargs

    @classmethod
    def _get(cls, **kwargs):
        order = kwargs["order"]

        products = []
        for order_detail in order.order_details:
            product = order_detail.product
            products.append(
                "%s, %s*%s"
                % (
                    product.name,
                    round(float(order_detail.price_net), 2),
                    int(order_detail.quantity_net),
                )
                if order_detail.quantity_net > 1
                else "%s, %s"
                % (product.name, round(float(order_detail.price_net), 2))
            )
        data = {
            "first": "您的订单提交成功！",
            "keyword1": order.shop.shop_name,
            "keyword2": order.update_at.strftime(DateFormat.TIME),
            "keyword3": "[" + "，".join(products) + "]",
            "keyword4": str(round(float(order.total_amount_net), 2)),
            "remark": "订单{}正在准备中,点击查看订单详情".format(order.order_num),
        }
        # 前端路由,前端路由变了这里有相应的改变
        url = urllib.parse.urljoin(
            WSC_HOST_NAME,
            "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
        )
        return url, data


# # 拼团成功的模板消息
# @register_celery()
# class GrouponOrderSuccessAttendTplMsg(TplMsgStrategy):
#     """拼团成功的模板消息"""
#
#     _tpl_format = ORDER_COMMIT
#     _default_template_id = (
#         "4QuRCzRuxVFWuz1gw8hHXlAaJZL4H2lLAyPXNr1MXIs"
#         if not debug
#         else "j33gYWAno6Q0_tqzWI40ZoAj3m39TEp-seWH_biCdBs"
#     )
#     _template_id_short = "OPENTM410958953"
#
#     @classmethod
#     def _middle_handler(cls, **kwargs):
#         order_id = kwargs["order_id"]
#         res, order = get_order_detail_by_id_only_msg_notify(order_id)
#         if not res:
#             raise ValueError("订单不存在")
#         to_user_id_list = [order.customer.user.id]
#         shop_id = order.shop.id
#         new_kwargs = {"order": order}
#
#         return to_user_id_list, shop_id, new_kwargs
#
#     @classmethod
#     def _get(cls, **kwargs):
#         order = kwargs["order"]
#
#         products = []
#         for order_detail in order.order_details:
#             product = order_detail.product
#             products.append(
#                 "%s, %s*%s"
#                 % (
#                     product.name,
#                     round(float(order_detail.price_net), 2),
#                     int(order_detail.quantity_net),
#                 )
#                 if order_detail.quantity_net > 1
#                 else "%s, %s"
#                 % (product.name, round(float(order_detail.price_net), 2))
#             )
#         data = {
#             "first": "拼团成功！",
#             "keyword1": order.shop.shop_name,
#             "keyword2": order.create_time.strftime(DateFormat.TIME),
#             "keyword3": "[" + "，".join(products) + "]",
#             "keyword4": str(round(float(order.total_amount_net), 2)),
#             "remark": "订单{}正在准备中,点击查看订单详情".format(order.order_num),
#         }
#         # 前端路由,前端路由变了这里有相应的改变
#         url = urllib.parse.urljoin(
#             WSC_HOST_NAME,
#             "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
#         )
#         return url, data


# 订单配送通知
@register_celery()
class OrderDeliveryTplMsg(TplMsgStrategy):
    """订单消息通知模板"""

    _tpl_format = ORDER_DELIVERY
    _default_template_id = (
        "bpnc40s6mmT30y-sgU4sEEqOEzKoP485IWSzzBLdHkk"
        if not debug
        else "O9FU1v95T2VTjm1p0un2duxvmVuPoCF4JyK1uvTaSkc"
    )
    _template_id_short = "OPENTM207710423"

    @classmethod
    def _middle_handler(cls, **kwargs):
        order_id = kwargs["order_id"]
        res, order = get_order_detail_by_id_only_msg_notify(order_id)
        if not res:
            raise ValueError("订单不存在")
        to_user_id_list = [order.customer.user.id]
        shop_id = order.shop.id
        new_kwargs = {"order": order}

        return to_user_id_list, shop_id, new_kwargs

    @classmethod
    def _get(cls, **kwargs):
        order = kwargs["order"]
        data = {
            "first": "您有一笔订单已完成准备，等待自提"
            if order.delivery_method == OrderDeliveryMethod.CUSTOMER_PICK
            else "您有一笔订单已安排配送"
            if order.delivery.delivery_type == DeliveryType.StaffDelivery
            else "您有一笔订单已安排发货",
            "keyword1": order.create_time.strftime(DateFormat.TIME),
            "keyword2": order.shop.shop_name,
            "keyword3": order.order_num,
            "keyword4": order.address.full_address,
            "remark": "自提时段：%s" % order.delivery_period_text
            if order.delivery_method == OrderDeliveryMethod.CUSTOMER_PICK
            else "商家配送"
            if order.delivery.delivery_type == DeliveryType.StaffDelivery
            else "%s %s" % (order.delivery.company, order.delivery.express_num),
        }
        # 前端路由,前端路由变了之后这里要相应改变
        url = urllib.parse.urljoin(
            WSC_HOST_NAME,
            "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
        )
        return url, data


# 订单完成消息通知
@register_celery()
class OrderFinishTplMsg(TplMsgStrategy):
    """订单完成消息通知模板"""

    _tpl_format = ORDER_FINISH
    _default_template_id = (
        "Bc9bSFi2M2_R39k6JnojeUYf3tuISaYtZ0qqsNKcUM0"
        if not debug
        else "qKBBLSOPmVfTtzvVageD0EYkU8nrTyHS8IzPm1rh7CU"
    )
    _template_id_short = "OPENTM202521011"

    @classmethod
    def _middle_handler(cls, **kwargs):
        order_id = kwargs["order_id"]
        res, order = get_order_detail_by_id_only_msg_notify(order_id)
        if not res:
            raise ValueError("订单不存在")
        to_user_id_list = [order.customer.user.id]
        shop_id = order.shop.id
        new_kwargs = {"order": order}

        return to_user_id_list, shop_id, new_kwargs

    @classmethod
    def _get(cls, **kwargs):
        order = kwargs["order"]
        data = {
            "first": "您在【{}】有一笔订单已完成".format(order.shop.shop_name),
            "keyword1": order.order_num,
            "keyword2": order.update_at.strftime(DateFormat.TIME),
            "remark": "可点击查看订单详情",
        }
        # 前端路由,前端路由变了之后这里要相应改变
        url = urllib.parse.urljoin(
            WSC_HOST_NAME,
            "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
        )
        return url, data


# 订单退款消息通知, 货到付款的不发送消息
@register_celery()
class OrderRefundTplMsg(TplMsgStrategy):
    """订单退款消息通知模板"""

    _tpl_format = ORDER_REFUND
    _default_template_id = (
        "G7sbLBTNGj_AENUiG9C53ShAWzUCC9SDh2B20lQ_Nvs"
        if not debug
        else "vwoSG7HipnL3q1Eff1P0RYeHfWuvs8cjbCKGO-gQxtA"
    )
    _template_id_short = "OPENTM200565278"

    @classmethod
    def _middle_handler(cls, **kwargs):
        order_id = kwargs["order_id"]
        res, order = get_order_detail_by_id_only_msg_notify(order_id)
        if not res:
            raise ValueError("订单不存在")
        to_user_id_list = [order.customer.user.id]
        shop_id = order.shop.id
        new_kwargs = {"order": order}

        return to_user_id_list, shop_id, new_kwargs

    @classmethod
    def _get(cls, **kwargs):
        order = kwargs["order"]
        data = {
            "first": "您在【{}】有一笔订单已退款".format(order.shop.shop_name),
            "keyword1": order.order_num,
            "keyword2": str(round(float(order.total_amount_net), 2)),
            "keyword3": "微信支付",
            "keyword4": "立即到账",
        }
        # 前端路由,前端路由变了之后这里要相应改变
        url = urllib.parse.urljoin(
            WSC_HOST_NAME,
            "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
        )
        return url, data


# # 拼团失败自动退款消息通知
# @register_celery()
# class GrouponOrderFailAttendTplMsg(TplMsgStrategy):
#     """拼团失败消息通知模板"""
#
#     _tpl_format = ORDER_REFUND
#     _default_template_id = (
#         "G7sbLBTNGj_AENUiG9C53ShAWzUCC9SDh2B20lQ_Nvs"
#         if not debug
#         else "vwoSG7HipnL3q1Eff1P0RYeHfWuvs8cjbCKGO-gQxtA"
#     )
#     _template_id_short = "OPENTM200565278"
#
#     @classmethod
#     def _middle_handler(cls, session, **kwargs):
#         order_id = kwargs["order_id"]
#         res, order = get_order_detail_by_id_only_msg_notify(session, order_id)
#         if not res:
#             raise ValueError("订单不存在")
#         to_user_id_list = [order.customer.user_id]
#         shop_id = order.shop.id
#         new_kwargs = {"order": order}
#
#         return to_user_id_list, shop_id, new_kwargs
#
#     @classmethod
#     def _get(cls, **kwargs):
#         order = kwargs["order"]
#         assert order.order_type == OrderType.GROUPON
#
#         data = {
#             "first": "您在【{}】有一笔订单拼团失败，已为您安排退款".format(order.shop.shop_name),
#             "keyword1": order.num,
#             "keyword2": str(round(float(order.total_amount_net), 2)),
#             "keyword3": "微信支付",
#             "keyword4": "立即到账",
#         }
#         # 前端路由,前端路由变了之后这里要相应改变
#         url = urllib.parse.urljoin(
#             WSC_HOST_NAME,
#             "/mall/?#/{}/orderDetail?id={}".format(order.shop.shop_code, order.id),
#         )
#         return url, data


# # 拼团订单自动退款失败消息通知
# @register_celery()
# class GrouponOrderRefundFailTplMsg(TplMsgStrategy):
#     """拼团订单自动退款失败消息通知"""
#
#     _tpl_format = REFUND_FAIL
#     _default_template_id = (
#         "CEWnYIwVJGhRhe-1gpszBVZ7bfVj8TRxechU4tKabcg"
#         if not debug
#         else "chiC0Q7CYSFYWDd0QhIirfoOJW9uVzdTJmQruP4b0kM"
#     )
#     _template_id_short = "OPENTM412546294"
#
#     @classmethod
#     def _middle_handler(cls, session, **kwargs):
#         order_id = kwargs["order_id"]
#         res, order = get_order_detail_by_id_only_msg_notify(session, order_id)
#         if not res:
#             raise ValueError("订单不存在")
#         shop_id = order.shop_id
#         staff_list = list_staff_by_shop_id_with_user(session, shop_id)
#         to_user_id_list = [staff.user_id for staff in staff_list]
#         new_kwargs = {"order": order}
#
#         return to_user_id_list, shop_id, new_kwargs
#
#     @classmethod
#     def _get(cls, **kwargs):
#         order = kwargs["order"]
#
#         data = {
#             "first": "订单拼团失败，因账号余额不足，无法自动退款",
#             "keyword1": order.num,
#             "keyword2": order.update_at.strftime(DateFormat.TIME),
#             "keyword3": str(round(float(order.total_amount_net), 2)),
#             "keyword4": "余额不足",
#             "remark": "请在电脑商户后台-订单板块查看处理",
#         }
#         url = None
#
#         return url, data
