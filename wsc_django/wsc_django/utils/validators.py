"""自定义验证器存放"""
import re

from rest_framework import serializers

from order.constant import OrderDeliveryMethod, OrderPayType
from shop.constant import ShopVerifyActive, ShopVerifyType, ShopStatus
from staff.services import cal_all_roles_without_super, cal_all_permission


#########全局相关###########
def mobile_validator(value):
    """电话号验证"""

    if not re.match(r'1[3-9]\d{9}', value):
        raise serializers.ValidationError("手机号格式不正确")


########商铺相关###########
def shop_status_validator(value):
    """商铺状态验证"""

    shop_status_list = [
        ShopStatus.NORMAL,
        ShopStatus.REJECTED
    ]
    if value not in shop_status_list:
        raise serializers.ValidationError("商铺状态有误")


def shop_verify_status_validator(value):
    """商铺认证状态验证"""

    shop_verify_status_list = [
        ShopVerifyActive.YES,
        ShopVerifyActive.CHECKING,
        ShopVerifyActive.REJECTED
    ]
    if value not in shop_verify_status_list:
        raise serializers.ValidationError("商铺认证状态有误")


def shop_verify_type_validator(value):
    """商铺认证状态验证"""

    shop_verify_status_list = [
        ShopVerifyType.ENTERPRISE,
        ShopVerifyType.INDIVIDUAL
    ]
    if value not in shop_verify_status_list:
        raise serializers.ValidationError("商铺认证类型有误")


########订单相关###########
def delivery_method_validator(value):
    """订单配送方式验证"""

    delivery_method_list = [
        OrderDeliveryMethod.HOME_DELIVERY,
        OrderDeliveryMethod.CUSTOMER_PICK,
    ]
    if value not in delivery_method_list:
        raise serializers.ValidationError("配送方式有误")


def order_pay_type_validator(value):
    """订单支付方式验证"""

    order_pay_type_list = [
        OrderPayType.WEIXIN_JSAPI,
        OrderPayType.ON_DELIVERY
    ]
    if value not in order_pay_type_list:
        raise serializers.ValidationError("订单支付方式有误")