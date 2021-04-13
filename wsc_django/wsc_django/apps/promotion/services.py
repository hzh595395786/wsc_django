from django_redis import get_redis_connection

from promotion.abstract import PromotionEventTemplate


# 商品正在正在进行的营销活动的键
PRODUCT_PROMOTION_KEY = "promotion:shop:{shop_id}:product:{product_id}"


def publish_product_promotion(
    shop_id: int, product_id: int, event: PromotionEventTemplate, ttl: int
):
    """
    发布一条营销活动
    :param shop_id:
    :param product_id:
    :param event:
    :param ttl:
    :return:
    """
    key = PRODUCT_PROMOTION_KEY.format(shop_id=shop_id, product_id=product_id)
    redis_conn = get_redis_connection("subscribe")
    redis_conn.mset(key, event.get_event())
    redis_conn.expire(key, ttl)