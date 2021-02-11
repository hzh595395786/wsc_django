from uuid import uuid4

from shop.models import Shop
from user.models import User
from shop.constant import (
    ShopStatus,
)


def create_shop(shop_info: dict, user: User):
    """
    创建一个店铺
    :param shop_info:{
        "shop_name": "name",
        "shop_img": "http://xxx",
        "shop_province": 420000,
        "shop_city": 420100,
        "shop_county": 420101,
        "shop_county": "光谷智慧谷一栋505",
        "description": "xxxx",
        "suggest_phone": "153xxxxxxxx",
        "shop_phone": "152xxxxxxxx",
        "super_admin_id": 1
    }
    :param user: 创建商铺的用户对象
    :return:
    """
    # 创建店铺
    # 随机一个店铺编码, 查一下,万一重复就再来一个
    while True:
        shop_code = str(uuid4())[-9:]
        shop = Shop.objects.filter(shop_code=shop_code)
        if not shop:
            break
    shop_info["shop_code"] = shop_code
    shop_info["shop_phone"] = user.phone
    shop_info["super_admin_id"] = user.id
    shop = Shop.objects.create(**shop_info)
    shop.save()
    return shop


def get_shop_by_shop_code(shop_code: str, only_normal: bool = True):
    """
    通过shop_code获取shop对象
    :param shop_code: 商铺编码
    :param only_normal: 只查询正常
    :return:
    """
    shop = Shop.objects.filter(shop_code=shop_code)
    if only_normal:
        shop = shop.filter(status=ShopStatus.NORMAL)
    shop = shop.first()
    return shop


def get_shop_by_shop_id(shop_id: int, filter_close: bool = True):
    """
    通过商铺id获取商
    :param shop_id: 商铺id
    :param filter_close: 不查询关闭的
    :return:
    """
    shop = Shop.objects.filter(id=shop_id)
    if filter_close:
        shop = shop.exclude(status=ShopStatus.CLOSED)
    shop = shop.first()
    return shop