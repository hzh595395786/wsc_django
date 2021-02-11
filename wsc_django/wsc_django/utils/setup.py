"""一些设置"""


def get_format_response_data(serializer_data: dict or object, success: bool):
    """自定义response返回数据的格式"""
    data = {"success": success}
    for k in serializer_data:
        data[k] = serializer_data[k]
    return data