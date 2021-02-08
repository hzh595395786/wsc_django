from uuid import uuid4

from shop.models import Shop
from user.models import User


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
    shop_info["super_admin"] = user
    shop = Shop.objects.create(**shop_info)
    shop.save()
    return shop