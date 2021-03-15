import datetime
import hashlib
import json
import urllib.parse
import uuid

import requests

from wsc_django.apps.settings import LCSW_HANDLE_HOST, LCSW_INST_NO, LCSW_INST_KEY
from wsc_django.utils.core import Emoji


def formatParaMap(paraMap, paraList, if_sort=False):
    """ 格式化参数，签名过程需要使用 """
    if if_sort:
        slist = sorted(paraList)
    else:
        slist = paraList
    buff = []
    for k in slist:
        v = paraMap[k]
        buff.append("{0}={1}".format(k, v))
    return "&".join(buff)


class LcswPay:
    """ 利楚支付 """

    @staticmethod
    def getStrForSignOfTradeNotice(ret_dict):
        """ 支付回调参数格式化 """
        paraList = [
            "return_code",
            "return_msg",
            "result_code",
            "pay_type",
            "user_id",
            "merchant_name",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "total_fee",
            "end_time",
            "out_trade_no",
            "channel_trade_no",
            "attach",
        ]
        return formatParaMap(ret_dict, paraList)

    @staticmethod
    def getJspayParas(
        order_num,
        open_id,
        create_time,
        total_fee,
        order_body,
        notify_url,
        merchant_no,
        terminal_id,
        access_token,
    ):
        """ 获取公众号支付参数的参数格式化 """
        parameters = {}
        parameters["pay_ver"] = "100"
        parameters["pay_type"] = "010"
        parameters["service_id"] = "012"
        parameters["merchant_no"] = merchant_no
        parameters["terminal_id"] = terminal_id
        parameters["terminal_trace"] = order_num  # 终端流水号，填写商户系统的订单号
        parameters["terminal_time"] = create_time
        parameters["total_fee"] = total_fee
        parameters["open_id"] = open_id
        parameters["order_body"] = (
            Emoji.filter_emoji(order_body).replace(" ", "").replace("&", "")
        )
        parameters["notify_url"] = notify_url
        parameters["attach"] = "SENGUOPRODUCT"
        paraList = [
            "pay_ver",
            "pay_type",
            "service_id",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "total_fee",
        ]
        str_sign = (
            formatParaMap(parameters, paraList) + "&access_token=%s" % access_token
        )
        parameters["key_sign"] = (
            hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower()
        )
        return parameters

    @staticmethod
    def getAuthOpenidUrl(merchant_no, terminal_id, access_token, redirect_uri):
        """ 获取利楚支付的公众号支付用户open_id的跳转地址 """
        str_sign = "merchant_no=%s&redirect_uri=%s&terminal_no=%s&access_token=%s" % (
            merchant_no,
            redirect_uri,
            terminal_id,
            access_token,
        )
        key_sign = hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower()
        parameters_str = (
            "merchant_no=%s&terminal_no=%s&&redirect_uri=%s&key_sign=%s"
            % (
                merchant_no,
                terminal_id,
                urllib.parse.quote(redirect_uri, safe="?"),
                key_sign,
            )
        )
        url = "%s/wx/jsapi/authopenid?%s" % (LCSW_HANDLE_HOST, parameters_str)
        return url

    @staticmethod
    def getStrForSignOfJspayRet(ret_dict):
        """ 公众号支付签名 """
        paraList = [
            "return_code",
            "return_msg",
            "result_code",
            "pay_type",
            "merchant_name",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "total_fee",
            "out_trade_no",
        ]
        buff = []
        for key in paraList:
            v = ret_dict[key] if ret_dict[key] else ""
            buff.append("{0}={1}".format(key, v))
        return "&".join(buff)

    @staticmethod
    def getRefundParas(
        pay_type,
        order_refund_num,
        out_trade_no,
        refund_fee,
        merchant_no,
        terminal_id,
        access_token,
    ):
        """ 获取退款参数 """
        parameters = {}
        parameters["pay_ver"] = "100"
        parameters["pay_type"] = pay_type
        parameters["service_id"] = "030"
        parameters["merchant_no"] = merchant_no
        parameters["terminal_id"] = terminal_id
        parameters["terminal_trace"] = order_refund_num  # 终端退款流水号，填写商户系统的退款流水号
        terminal_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        parameters["terminal_time"] = terminal_time
        parameters["refund_fee"] = refund_fee
        parameters["out_trade_no"] = out_trade_no  # 订单号，查询凭据，利楚订单号、微信订单号、支付宝订单号任意一个
        paraList = [
            "pay_ver",
            "pay_type",
            "service_id",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "refund_fee",
            "out_trade_no",
        ]
        str_sign = (
            formatParaMap(parameters, paraList, False)
            + "&access_token=%s" % access_token
        )
        parameters["key_sign"] = (
            hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower()
        )
        return parameters

    @staticmethod
    def getStrForSignOfRefundRet(ret_dict):
        """ 退款返回签名字符串 """
        paraList = [
            "return_code",
            "return_msg",
            "result_code",
            "pay_type",
            "merchant_name",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "refund_fee",
            "end_time",
            "out_trade_no",
            "out_refund_no",
        ]
        buff = []
        for key in paraList:
            v = ret_dict[key] if ret_dict[key] else ""
            buff.append("{0}={1}".format(key, v))
        return "&".join(buff)

    @staticmethod
    def getQueryParas(
        pay_type,
        order_query_num,
        out_trade_no,
        merchant_no,
        terminal_id,
        access_token,
        pay_trace="",
        pay_time="",
    ):
        """ 获取订单查询参数 """
        parameters = {}
        parameters["pay_ver"] = "100"
        parameters["pay_type"] = pay_type
        parameters["service_id"] = "020"
        parameters["merchant_no"] = merchant_no
        parameters["terminal_id"] = terminal_id
        parameters["terminal_trace"] = order_query_num  # 终端查询流水号，填写商户系统的查询流水号
        terminal_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        parameters["terminal_time"] = terminal_time
        parameters[
            "out_trade_no"
        ] = out_trade_no  # 订单号，查询凭据，可填利楚订单号、微信订单号、支付宝订单号、银行卡订单号任意一个
        parameters["pay_trace"] = pay_trace  # 当前支付终端流水号，与pay_time同时传递,该字段可以传32位,文档有误
        parameters[
            "pay_time"
        ] = pay_time  # 当前支付终端交易时间，yyyyMMddHHmmss，全局统一时间格式，与pay_trace同时传递
        paraList = [
            "pay_ver",
            "pay_type",
            "service_id",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "out_trade_no",
        ]
        str_sign = (
            formatParaMap(parameters, paraList, False)
            + "&access_token=%s" % access_token
        )
        parameters["key_sign"] = (
            hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower()
        )
        return parameters

    @staticmethod
    def getStrForSignOfQueryRet(ret_dict):
        paraList = [
            "return_code",
            "return_msg",
            "result_code",
            "pay_type",
            "merchant_name",
            "merchant_no",
            "terminal_id",
            "terminal_trace",
            "terminal_time",
            "total_fee",
            "end_time",
            "out_trade_no",
        ]
        buff = []
        for key in paraList:
            v = ret_dict[key] if ret_dict[key] else ""
            buff.append("{0}={1}".format(key, v))
        return "&".join(buff)


class LcswFunds:
    @staticmethod
    def queryWithdrawal(merchant_no):
        if not merchant_no:
            return {"return_code": "02", "return_msg": "商户号不能为空", "result_code": "02"}
        url = LCSW_HANDLE_HOST.rstrip("/") + "/merchant/100/withdraw/query"
        paralist = ["inst_no", "trace_no", "merchant_no"]
        data = dict(
            inst_no=LCSW_INST_NO, trace_no=uuid.uuid4().hex, merchant_no=merchant_no
        )
        str_sign = "{}&key={}".format(
            formatParaMap(data, paralist, True), LCSW_INST_KEY
        )
        data["key_sign"] = hashlib.md5(str_sign.encode("utf-8")).hexdigest()
        r = requests.post(url=url, json=data, timeout=(1, 10))
        result = json.loads(r.text)
        return result
