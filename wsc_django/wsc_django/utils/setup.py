"""一些设置相关"""
from rest_framework import serializers


class ConvertDecimalPlacesField(serializers.DecimalField):
    """将decimal转化为2位输出"""

    def to_representation(self, value):
        return round(float(value), 2)

