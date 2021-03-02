"""一些项目需要的类和方法"""
from rest_framework import serializers


class ConvertDecimalPlacesField(serializers.DecimalField):
    """将decimal转化为2位输出"""

    def to_representation(self, value):
        return round(float(value), 2)


def str_to_list(value, default, split_str: str = ",", if_int: bool = True,):
    """字符串转列表list(int)"""
    trans_type = int if if_int else str
    # 如果未传参则使用默认
    if not value:
        return True, default
    if not isinstance(value, (str, bytes)):
        return False, {'messages':"参数类型只能为字符串"}
    try:
        res_list = []
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        value = value.replace(" ", "")
        value_list = value.split(split_str) if value else []
        for v in value_list:
            res_list.append(trans_type(v))
        return True, res_list
    except Exception as e:
        return False, {'messages':e}



def is_contains(compare_list: list, compared_list: list):
    """
    判断需要比较的列表中的元素是否包含于被比较的列表
    :param compare_list: 需要比较的列表
    :param compared_list: 被比较的列表
    :return:
    """
    for el in compare_list:
        if el not in compared_list:
            return False
    return True
