import asyncio
import aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from django.core import signing

from settings import REDIS_SERVER, REDIS_PORT
from ws.constant import CHANNEL_ADMIN


RAISE_ERROR = object()


class AdminWebSocketConsumer(AsyncWebsocketConsumer):
    """后台websocket"""

    async def reader(self, ch):
        while await ch.wait_message():
            msg = await ch.get_json()
            await self.receive(msg)

    async def connect(self):
        self.sub = await aioredis.create_redis(
            (REDIS_SERVER, REDIS_PORT), db=10,
        )
        res = await self.sub.subscribe(CHANNEL_ADMIN)
        self.tsk = asyncio.create_task(self.reader(res[0]))
        await self.accept()

    async def disconnect(self, close_code):
        self.tsk.cancel()
        self.sub.close()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data == "ping":
            await self.send(json.dumps({"event": "pong", "data": "pong"}))
        else:
            key = "wsc_shop_id"
            salt = "微商城商铺id"
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
                await self.send(json.dumps({"event": text_data["event"], "data": text_data["data"]}))