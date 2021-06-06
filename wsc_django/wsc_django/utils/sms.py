"""短信第三方接口"""
import random

import requests
from qcloudsms_py import SmsSingleSender

from wsc_django.apps.settings import (
    TENCENT_SMS_APPID,
    TENCENT_SMS_APPKEY,
    YUNPIAN_SYSTEM_APIKEY,
)

# 短信签名
yunpian_sms_common_sign = "【志浩web开发】"
tencent_sms_common_sign = "【志浩web开发】"


class YunPianSms:
    """云片短信"""

    # 服务地址
    sms_host = "sms.yunpian.com"
    voice_host = "voice.yunpian.com"
    # 版本号
    version = "v2"
    # 模板短信接口的URI
    sms_tpl_send_uri = "/{}/sms/tpl_single_send.json".format(version)
    sms_text_send_uri = "/{}/sms/single_send.json".format(version)
    # 获取短信接口的URI
    sms_short_url_uri = "/{}/short_url/shorten.json".format(version)
    # 营销短信群发URI
    sms_marketing_group_send_uri = "/{}/sms/tpl_batch_send.json".format(version)

    @classmethod
    def tpl_send_sms(cls, tpl_id, tpl_value, mobile, apikey=YUNPIAN_SYSTEM_APIKEY):
        """
        模板接口发短信（模版id传入）
        """
        # 短信中不能包含【 和】，发送前进行替换
        tpl_value = tpl_value.replace("【", "[")
        tpl_value = tpl_value.replace("】", "]")
        params = {
            "apikey": apikey,
            "tpl_id": tpl_id,
            "tpl_value": tpl_value,
            "mobile": mobile,
        }
        try:
            res = requests.post(
                "http://" + cls.sms_host + cls.sms_tpl_send_uri,
                data=params,
                timeout=(1, 5),
            )
        except:
            return False, "短信发送接口超时或异常, 请稍后重试"
        response = res.json()
        if response.get("code", 1) == 0:
            return True, ""
        else:
            return False, response.get("detail", "验证码发送失败，请稍后再试")

    @classmethod
    def tpl_send_sms_with_text(
        cls, tpl_value, mobile, sign_type=yunpian_sms_common_sign, apikey=YUNPIAN_SYSTEM_APIKEY
    ):
        """
        模板接口发短信（文本传入）
        """
        # 短信中不能包含【 和】，发送前进行替换
        tpl_value = tpl_value.replace("【", "[")
        tpl_value = tpl_value.replace("】", "]")
        params = {
            "apikey": apikey,
            "mobile": mobile,
            "text": "{}{}".format(sign_type, tpl_value),
        }
        try:
            res = requests.post(
                "http://" + cls.sms_host + cls.sms_text_send_uri,
                data=params,
                timeout=(1, 5),
            )
        except:
            return False, "短信发送接口超时或异常, 请稍后重试"
        response = res.json()
        if response.get("code", 1) == 0:
            return True, ""
        else:
            return False, response.get("detail", "验证码发送失败，请稍后再试")

    @classmethod
    def tpl_short_url(cls, long_url, apikey=YUNPIAN_SYSTEM_APIKEY):
        """获取短链接"""
        params = {"apikey": apikey, "long_url": long_url}
        try:
            res = requests.post(
                "http://" + cls.sms_host + cls.sms_short_url_uri,
                data=params,
                timeout=(1, 5),
            )
        except:
            return False, "短信发送接口超时或异常, 请稍后重试"
        response = res.json()
        if response.get("code", 1) == 0:
            return True, response["short_url"]["short_url"]
        else:
            return False, long_url

    @classmethod
    def tpl_send_sms_ret(cls, tpl_id, mobile, tpl_value, apikey=YUNPIAN_SYSTEM_APIKEY):
        """
            单条发送接口，返回实际发送消耗的短信条数或发送失败原因
        """
        params = {
            "apikey": apikey,
            "mobile": mobile,
            "tpl_value": tpl_value,
            "tpl_id": tpl_id,
        }
        try:
            res = requests.post(
                "https://" + cls.sms_host + cls.sms_tpl_send_uri,
                data=params,
                timeout=(1, 5),
            )
        except:
            return False, "短信发送接口超时或返回异常，请稍后再试"
        response = res.json()
        if response.get("code", 1) == 0:
            return True, response.get("count", 1)
        else:
            return False, response.get("detail") or response.get("msg", "短信发送失败，原因未知")

    @classmethod
    def send_sms_branch_ret(
        cls, tpl_id, mobiles, tpl_value, callback_url=None, apikey=YUNPIAN_SYSTEM_APIKEY
    ):
        """
        群发接口，返回所有结果
        :param apikey: 用户唯一标识，在管理控制台获取
        :param tpl_id: 模板id
        :param mobiles: 单号码：15205201314 多号码：15205201314,15205201315
        :param text: 已审核短信模板
        :param callback_url: 短信发送后将向这个地址推送发送报告, 这个接口好像是同步接口，直接返回结果。。。异步回调还有必要吗？
        :return: total_count, total_fee, unit, data
        """
        params = {
            "apikey": apikey,
            "tpl_id": tpl_id,
            "mobile": mobiles,
            "tpl_value": tpl_value,
        }
        if callback_url:
            params["callback_url"] = callback_url
        headers = {
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8;",
            "Accept": "application/json;charset=utf-8;",
            "Connection": "keep-alive",
        }
        try:
            res = requests.post(
                "https://" + cls.sms_host + cls.sms_marketing_group_send_uri,
                data=params,
                headers=headers,
            )
        except:
            return False, "短信发送接口超时或返回异常，请稍后再试"
        response = res.json()
        total_count = response.get("total_count", 0)
        data = response.get("data", [])
        return True, (total_count, data)

    @classmethod
    def send_yunpian_verify_code(cls, mobile, code, use, mode="text"):
        """发送短信验证码，模版内容：
        【微商城助手】您的验证码是#code#。此验证码用于绑定手机号，5分钟内有效。
        ps:这个单独用了一个不一样的签名，现在审核模版必须要加图形验证码，狗带 2018-07-19 by yy
        """
        if mode == "text":
            tpl_value = "您的验证码是{code}。此验证码用于绑定手机号".format(code=code)
            return cls.tpl_send_sms_with_text(tpl_value, mobile)
        else:
            tpl_id = 4460930
            tpl_value = "#code#={}&#use#={}".format(code, use)
            return cls.tpl_send_sms(tpl_id, tpl_value, mobile)


class TencentSms:
    """腾讯短信"""

    # 创建接口调用对象
    ssender = SmsSingleSender(TENCENT_SMS_APPID, TENCENT_SMS_APPKEY)

    @classmethod
    def tpl_send_sms(cls, sms_text, mobile, smsType=0, smsSign=tencent_sms_common_sign):
        """ 单发短信接口
        :param text string 短信内容
        :param mobile string 手机号
        :param smsType int 签名类型  0: 普通短信, 1: 营销短信
        :param smsSign string 签名内容
        :rtype True or errmsg
        """
        # 短信中不能包含【 和】，发送前进行替换
        sms_text = sms_text.replace("【", "[")
        sms_text = sms_text.replace("】", "]")
        # 拼接签名和短信内容
        sms_text = "{}{}".format(smsSign, sms_text)
        try:
            # 返回结果{'result': 1014, 'errmsg': 'package format error, sdkappid not have this tpl_id', 'ext': ''}
            result = cls.ssender.send(
                smsType, 86, mobile, sms_text, extend="", ext=""
            )  # 签名参数未提供或者为空时，会使用默认签名发送短信
        except:
            return False, "短信发送接口超时或返回异常，请稍后再试"

        result_code = result["result"]
        if result_code == 0:
            return True, ""
        else:
            return False, result["errmsg"]

    @classmethod
    def send_tencent_verify_code(cls, mobile, code, use):
        """ 发送短信验证码
        模版内容：您的验证码是#code#。此验证码用于#use#，5分钟内有效。

        param: mobile 手机号
        param: code 验证码
        param: use 验证码用途
        """
        sms_text = "您的验证码是{code}。此验证码用于绑定手机号，5分钟内有效。".format(code=code)
        return cls.tpl_send_sms(sms_text, mobile)


def gen_sms_code():
    population_seq = "0123456789"  # 组成验证码元素的序列
    code_length = 4  # 验证码长度

    code = "".join([random.choice(population_seq) for i in range(code_length)])
    return code
