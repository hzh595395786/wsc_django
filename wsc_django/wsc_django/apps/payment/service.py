import hashlib
import json

import requests

from order.constant import OrderStatus
from order.models import Order
from order.selectors import get_order_by_num_for_update
from payment.models import OrderTransaction
from shop.models import Shop
from shop.services import get_shop_by_shop_id
from user.services import get_pay_channel_by_shop_id
from wsc_django.apps.settings import LCSW_CALLBACK_HOST, LCSW_HANDLE_HOST
from wsc_django.utils.lcsw import LcswPay
from wsc_django.utils.core import NumGenerator


def create_order_transaction(
        order_id, transaction_id, receipt_fee, channel_trade_no
):
    """
    创建订单交易记录
    :param order_id:
    :param transaction_id:
    :param receipt_fee:
    :param channel_trade_no:
    :return:
    """
    order_transaction = OrderTransaction(
        order_id=order_id,
        transaction_id=transaction_id,
        receipt_fee=receipt_fee,
        channel_trade_no=channel_trade_no,
    )
    order_transaction.save()
    return order_transaction


def get_openid_redirect_url(shop: Shop, redirect: str):
    """
    获取openid需要的重定向URL
    :param shop:
    :param redirect:
    :return:
    """
    success, pay_channel = get_pay_channel_by_shop_id(shop.id)
    if not success:
        return False, pay_channel
    lc_redirect_uri = "{host}/mall/{shop_code}/openid/lcsw/?redirect={redirect}".format(
        host=LCSW_CALLBACK_HOST,
        shop_code=shop.shop_code,
        redirect=redirect,
    )
    result = LcswPay.getAuthOpenidUrl(
        pay_channel.smerchant_no,
        pay_channel.terminal_id1,
        pay_channel.access_token,
        lc_redirect_uri,
    )
    return True, result


def handle_lcsw_callback(res_dict: dict):
    """
    处理利楚回调
    :param res_dict:
    :return:
    """
    # 业务结果检查
    if res_dict["return_code"] == "02":
        raise ValueError("LcCallBackFail", res_dict["return_msg"])
    # 附加信息检查
    if res_dict["attach"] != "SENGUOPRODUCT":
        raise ValueError("LcCallBackFail", "附加信息有误")
    # 订单有效性检查
    num = res_dict["terminal_trace"]
    order = get_order_by_num_for_update(num)
    if not order:
        raise ValueError("LcCallBackFail", "订单不存在: {}".format(num))
    elif order.status != OrderStatus.UNPAID:
        raise ValueError("LcCallBackFail", "订单状态错误: {}".format(order.status))
    # 店铺检查及验签
    shop_id, _ = NumGenerator.decode(num)
    shop = get_shop_by_shop_id(shop_id)
    if not shop:
        raise ValueError("LcCallBackFail", "找不到对应的店铺")
    success, pay_channel = get_pay_channel_by_shop_id(shop_id)
    if not success:
        raise ValueError("LcCallBackFail", pay_channel)
    key_sign = res_dict["key_sign"]
    str_sign = (
            LcswPay.getStrForSignOfTradeNotice(res_dict)
            + "&access_token=%s" % pay_channel.access_token
    )
    if key_sign != hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower():
        raise ValueError("LcCallBackFail", "签名有误")
    # 检查业务结果：01成功 02失败
    result_code = res_dict["result_code"]
    if result_code == "02":
        raise ValueError("LcCallBackFail", res_dict["return_msg"])

    # TODO: 考虑是否进行回调的幂等检查
    create_order_transaction(
        order.id,
        res_dict["out_trade_no"],
        res_dict["receipt_fee"],
        res_dict["channel_trade_no"],
    )
    return True, order


def payment_query(order: Order):
    """
    订单查询支付情况， 直接返回字典
    :param order:
    :return: 类型说明:0-支付查询中|1-支付出错|2-支付成功
             字典说明:out_trade_no,channel_trade_no必有的；0/1,+msg;2,+total_fee
    """
    success, pay_channel = get_pay_channel_by_shop_id(order.shop.id)
    if not success:
        return 1, pay_channel
    pay_type = "010"
    params = LcswPay.getQueryParas(
        pay_type,
        order.order_num,
        "",
        pay_channel.smerchant_no,
        pay_channel.terminal_id1,
        pay_channel.access_token,
        pay_trace=order.order_num,
        pay_time=order.create_time.strftime("%Y%m%d%H%M%S"),
    )
    ret_dict = {}
    try:
        r = requests.post(
            LCSW_HANDLE_HOST + "/pay/100/query",
            data=json.dumps(params),
            verify=False,
            headers={"content-type": "application/json"},
            timeout=(1, 5),
        )
        res_dict = json.loads(r.text)
    except BaseException:
        ret_dict["msg"] = "正在查询支付结果，请稍候(LCER1)..."
        return 0, ret_dict

    ret_dict["out_trade_no"] = res_dict.get("out_trade_no", "")
    ret_dict["channel_trade_no"] = res_dict.get("channel_trade_no", "")
    # 响应码：01成功 02失败，响应码仅代表通信状态，不代表业务结果
    if res_dict["return_code"] == "02":
        if res_dict["return_msg"] == "订单信息不存在！":
            ret_dict["msg"] = "等待用户付款中，请提醒用户在手机上完成支付..."
            return 0, ret_dict
        else:
            ret_dict["msg"] = res_dict["return_msg"]
            return 1, ret_dict

    key_sign = res_dict["key_sign"]
    for key in res_dict:
        if res_dict[key] is None:
            res_dict[key] = "null"
    str_sign = LcswPay.getStrForSignOfQueryRet(res_dict)
    if key_sign != hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower():
        ret_dict["msg"] = "签名错误"
        return 1, ret_dict

    # 业务结果：01成功 02失败 03支付中
    result_code = res_dict["result_code"]
    if result_code == "02":
        ret_dict["msg"] = res_dict["return_msg"]
        return 1, ret_dict
    elif result_code == "03":
        ret_dict["msg"] = "等待用户付款中，请提醒用户在手机上完成支付..."
        return 0, ret_dict
    else:
        ret_dict["total_fee"] = int(res_dict["total_fee"])
        return 2, ret_dict


def get_wx_jsApi_pay(order: Order, wx_openid: str):
    """
    公众号支付参数获取
    :param order:
    :param wx_openid:
    :return:
    """
    shop = get_shop_by_shop_id(order.shop.id)
    success, pay_channel = get_pay_channel_by_shop_id(order.shop.id)
    if not success:
        return False, pay_channel
    body = "{}-订单号-{}".format(shop.shop_name, order.order_num)
    notify_url = "{}/payment/lcsw/callback/order/".format(LCSW_CALLBACK_HOST)
    parameters = LcswPay.getJspayParas(
        order.order_num,
        wx_openid,
        order.create_time.strftime("%Y%m%d%H%M%S"),
        int(round(order.total_amount_net * 100)),
        body,
        notify_url,
        pay_channel.smerchant_no,
        pay_channel.terminal_id1,
        pay_channel.access_token,
    )

    try:
        r = requests.post(
            LCSW_HANDLE_HOST + "/pay/100/jspay",
            data=json.dumps(parameters),
            verify=False,
            headers={"content-type": "application/json"},
            timeout=(1, 5),
        )
        res_dict = json.loads(r.text)
    except BaseException:
        return False, "微信支付预下单失败：接口超时或返回异常（LC）"

        # 响应码：01成功 ，02失败，响应码仅代表通信状态，不代表业务结果
    if res_dict["return_code"] == "02":
        return (
            False,
            "微信支付通信失败：{msg}".format(msg=res_dict["return_msg"]),
        )

    key_sign = res_dict["key_sign"]
    str_sign = LcswPay.getStrForSignOfJspayRet(res_dict)
    if key_sign != hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower():
        return False, "微信支付校验失败：签名错误（LC）"

    # 业务结果：01成功 02失败
    result_code = res_dict["result_code"]
    if result_code == "02":
        return (False, "微信支付业务失败：{msg}".format(msg=res_dict["return_msg"]))

    renderPayParams = {
        "appId": res_dict["appId"],
        "timeStamp": res_dict["timeStamp"],
        "nonceStr": res_dict["nonceStr"],
        "package": res_dict["package_str"],
        "signType": res_dict["signType"],
        "paySign": res_dict["paySign"],
    }
    return True, renderPayParams


def get_order_transaction_by_order_id(order_id: int):
    """
    通过订单id获取交易记录
    :param order_id:
    :return:
    """
    order_transaction = OrderTransaction.objects.filter(order_id=order_id).first()
    return order_transaction

