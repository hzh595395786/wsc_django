"""自定义验证器存放"""
import re

from rest_framework import serializers

from shop.constant import ShopVerifyActive, ShopVerifyType, ShopStatus


def mobile_validator(value):
    """电话号验证"""

    if not re.match(r'1[3-9]\d{9}', value):
        raise serializers.ValidationError("手机号格式不正确")


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

