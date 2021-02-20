"""一些设置相关"""
from rest_framework import serializers


def get_format_response_data(
        serializer_data: dict or object or list,
        success: bool,
        many: bool = False
):
    """自定义response返回数据的格式"""
    response_data = {"success": success}
    if many:
        for i in serializer_data:
            data = {}
            data_list = []
            data_list.append(ReturnedDict_to_dict(data, i))
        response_data["data_list"] = data_list
    else:
        ReturnedDict_to_dict(response_data, serializer_data)
    return response_data


def ReturnedDict_to_dict(data:dict, serializer_data: dict or object):
    """将序列化后的ReturnedDict转换为python的dict"""
    for k in serializer_data:
        data[k] = serializer_data[k]
    return data


class ConvertDecimalPlacesField(serializers.DecimalField):
    """将decimal转化为2位输出"""

    def to_representation(self, value):
        return round(float(value), 2)

