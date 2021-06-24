import asyncio
import aioredis
import json

from channels.generic.websocket import WebsocketConsumer
from django.core import signing
from asgiref.sync import async_to_sync

from settings import REDIS_SERVER, REDIS_PORT
from ws.constant import CHANNEL_ADMIN


RAISE_ERROR = object()


class AdminWebSocketConsumer(WebsocketConsumer):
    """后台websocket"""

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            CHANNEL_ADMIN, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            CHANNEL_ADMIN, self.channel_name
        )

    def send_message(self, event):
        # 服务器向前端发送信息
        message = event['message']
        self.receive(message)

    def receive(self, text_data=None, bytes_data=None):
        if text_data == "ping":
            self.send(json.dumps({"event": "pong", "data": "pong"}))
        else:
            key = "wsc_shop_id"
            salt = "hzh_wsc_shop_id"
            default = RAISE_ERROR
            cookie_value = self.scope["cookies"].get(key)
            try:
                cookie_shop_id = signing.get_cookie_signer(salt=key + salt).unsign(
                    cookie_value, max_age=None)
            except signing.BadSignature:
                if default is not RAISE_ERROR:
                    return default
                else:
                    raise
            if str(text_data["shop_id"]) == str(cookie_shop_id):
                self.send(json.dumps({"event": text_data["event"], "data": text_data["data"]}))