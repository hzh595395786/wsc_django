import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from ws.constant import CHANNEL_ADMIN


def publish_admin(shop_id: int, event: str, data: dict):
    """

    :param shop_id: 商铺id，在接收端控制
    :param event: str, 事件名
    :param data: `事件中需要发布的数据，为简便，暂为字符串`
    :return:
    """
    message = {"shop_id": shop_id, "event": event, "data": data}
    channels_layer = get_channel_layer()
    send_dic = {
        "type": "send.message",
        "message": message,
    }
    async_to_sync(channels_layer.group_send)(CHANNEL_ADMIN, send_dic)