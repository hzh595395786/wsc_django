"""项目要用到的一些类和函数"""
from rest_framework import serializers


class FuncField(serializers.Field):
    """传入一个匿名函数，将该字段接收的值用函数转换"""

    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func

    def to_representation(self, value):
        return self.func(value)
