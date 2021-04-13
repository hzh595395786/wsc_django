from uuid import uuid4
from django.db.models import Count

from product.constant import ProductStatus
from shop.models import Shop, HistoryRealName, ShopRejectReason, PayChannel
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
        "shop_address": "光谷智慧谷一栋505",
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


def create_pay_channel(pay_channel_info: dict, shop_id: int):
    """
    创建一个商铺的pay_channel
    :param pay_channel_info:
    :param shop_id:
    :return:
    """
    shop_pay_channel = PayChannel.objects.create(shop_id=shop_id, **pay_channel_info)
    shop_pay_channel.save()
    return shop_pay_channel


def create_shop_reject_reason_by_shop_id(shop: Shop, reject_reason: str):
    """
    给拒绝的店铺创建一个拒绝理由
    :param shop_id:
    :return:
    """
    reject_reason = ShopRejectReason.objects.create(id=shop, reject_reason=reject_reason)
    return reject_reason


def update_shop_data(shop: Shop, args: dict):
    """
    修改店铺信息
    :param shop:
    :param args:
    :return:
    """
    for k, v in args.items():
        setattr(shop, k, v)
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
    if shop and only_normal:
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
    if shop and filter_close:
        shop = shop.exclude(status=ShopStatus.CLOSED)
    shop = shop.first()
    return shop


def list_shop_by_shop_ids(shop_ids: list, filter_close: bool = True):
    """
    通过ship_id列表查询店铺列表
    :param shop_ids:
    :param filter_close:过滤关闭
    :return:
    """
    shop_list_query = Shop.objects.filter(id__in=shop_ids)
    if shop_list_query and filter_close:
        shop_list_query = shop_list_query.exclude(status=ShopStatus.CLOSED)
    shop_list = shop_list_query.all()
    return shop_list


def get_shop_product_species_count_by_shop_ids(shop_ids: list):
    """
    通过店铺id列表查找商铺的货品种类数量
    :param shop_ids: 商铺id列表
    :return:
    """
    shop_product_count = (
        Shop.objects.filter(id__in=shop_ids).
        exclude(product__status=ProductStatus.DELETED).
        annotate(product_count=Count("product"))
    )
    shop_product_count_dict = {
        shop.id:shop.product_count for shop in shop_product_count
    }
    return shop_product_count_dict


def list_shop_by_shop_status(shop_status: int):
    """
    查询某一状态的所有店铺
    :param shop_status:
    :return:
    """
    shop_list = Shop.objects.filter(status=shop_status).order_by('update_at').all()
    return shop_list


def list_shop_creator_history_realname(shop_ids: list):
    """
    找出店铺创建的历史真实姓名列表
    :param shop_ids:
    :return:
    """
    history_realname_list = (
        HistoryRealName.objects.filter(id__in=shop_ids).all()
    )
    return history_realname_list


def list_shop_reject_reason(shop_ids: list):
    """查询出所有的店铺拒绝信息"""
    reject_reason_list = ShopRejectReason.objects.filter(id__in=shop_ids).all()
    return reject_reason_list