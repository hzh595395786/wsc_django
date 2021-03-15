import random
import string
import time

from django_redis import get_redis_connection
from webargs.djangoparser import use_args
from webargs import fields
from wechatpy import WeChatClient

from wsc_django.apps.settings import MP_APPID, MP_APPSECRET
from wsc_django.utils.views import GlobalBaseView


class WechatJsapiSigntureView(GlobalBaseView):
    """商城-获取微信jsapi"""

    @use_args({"url": fields.String(required=True, comment="当前页面的URL")}, location="query")
    def get(self, request, args):
        redis_conn = get_redis_connection("default")
        access_token = redis_conn.get("access_token")
        access_token = access_token.decode("utf-8") if access_token else None
        wechat_client = WeChatClient(
            appid=MP_APPID, secret=MP_APPSECRET, access_token=access_token, timeout=5
        )
        if not access_token:
            access_token = wechat_client.fetch_access_token()
            redis_conn.setex("access_token", 3600, access_token.get("access_token"))
        jsapi_ticket = redis_conn.get("jsapi_ticket")
        jsapi_ticket = jsapi_ticket.decode("utf-8") if jsapi_ticket else None
        if not jsapi_ticket:
            jsapi_ticket = wechat_client.jsapi.get_jsapi_ticket()
            redis_conn.setex("jsapi_ticket", 7100, jsapi_ticket)
        noncestr = "".join(random.sample(string.ascii_letters + string.digits, 10))
        timestamp = int(time.time())
        signature = wechat_client.jsapi.get_jsapi_signature(
            noncestr, jsapi_ticket, timestamp, args.get("url")
        )
        data = {
            "appID": MP_APPID,
            "timestamp": timestamp,
            "nonceStr": noncestr,
            "signature": signature,
        }

        return self.send_success(data=data)
