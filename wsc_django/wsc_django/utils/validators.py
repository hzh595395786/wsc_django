"""自定义验证器存放"""
import re

from rest_framework import serializers


def mobile_validator(value):
    """电话号验证"""
    if not re.match(r'1[3-9]\d{9}', value):
        raise serializers.ValidationError("手机号格式不正确")