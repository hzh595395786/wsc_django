from django_redis import get_redis_connection

from product.models import Product
from promotion.abstract import PromotionEventTemplate
from promotion.events import GrouponEvent


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
    redis_conn.hmset(key, event.get_event())
    redis_conn.expire(key, ttl)


def stop_product_promotion(shop_id: int, product_id: int) -> None:
    """
    停用一个正在进行中的营销活动
    :param shop_id: 店铺id
    :param product_id: 商品id
    """
    key = PRODUCT_PROMOTION_KEY.format(shop_id=shop_id, product_id=product_id)
    redis_conn = get_redis_connection("subscribe")
    redis_conn.delete(key)


def set_product_promotion(product: Product, promotion: PromotionEventTemplate):
    """
    校验营销活动，并给商品添加营销活动信息
    :param product:
    :param promotion:
    :return:
    """
    if not promotion:
        return
    if isinstance(promotion, GrouponEvent):
        if (
            hasattr(promotion, "success_limit")
            and int(promotion.success_limit) != 0
            and int(promotion.success_limit) <= int(promotion.succeeded_count)
        ):
            return
        product.groupon = promotion
    else:
        raise ValueError("Unknown promotion type")


def get_product_promotion(shop_id: int, product_id: int):
    """
    获取单个店铺正在进行的营销活动
    :param shop_id:
    :param product_id:
    :return:
    """
    pattern = PRODUCT_PROMOTION_KEY.format(shop_id=shop_id, product_id=product_id)
    redis_conn = get_redis_connection("subscribe")
    if redis_conn.hlen(pattern):
        redis_event_dict = redis_conn.hgetall(pattern)
        event_dict = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in redis_event_dict.items()
        }
        if event_dict["event_type"] == GrouponEvent._event_type:
            event = GrouponEvent(event_dict)
        else:
            raise ValueError("Unknown event type")
        return event
    else:
        return None


def list_product_promotions(shop_id: int):
    """
    获取店铺所有商品正在进行营销活动
    :param shop_id:
    :return:
    """
    pattern = PRODUCT_PROMOTION_KEY.format(shop_id=shop_id, product_id="*")
    redis_conn = get_redis_connection("subscribe")
    keys = redis_conn.keys(pattern)
    result = {}
    for key in keys:
        *_, product_id = key.decode("utf-8").split(":")
        redis_event_dict = redis_conn.hgetall(key)
        event_dict = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in redis_event_dict.items()
        }
        # 不同类型的时间返回不同的类
        if event_dict["event_type"] == GrouponEvent._event_type:
            event = GrouponEvent(event_dict)
        else:
            raise ValueError("Unknown event type")
        result[int(product_id)] = event
    return result
