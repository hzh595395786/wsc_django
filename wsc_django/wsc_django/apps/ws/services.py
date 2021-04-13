import json

from django_redis import get_redis_connection

from ws.constant import CHANNEL_ADMIN


def publish_admin(shop_id: int, event: str, data: dict):
    """

    :param shop_id: 商铺id，在接收端控制
    :param event: str, 事件名
    :param data: `事件中需要发布的数据，为简便，暂为字符串`
    :return:
    """
    message = json.dumps({"shop_id": shop_id, "event": event, "data": data})
    redis_conn = get_redis_connection("subscribe")
    redis_conn.publish(CHANNEL_ADMIN, message)