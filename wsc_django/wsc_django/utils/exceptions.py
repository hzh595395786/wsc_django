"""异常处理"""
from django.db.utils import DatabaseError
from rest_framework import exceptions
from django.db.transaction import TransactionManagementError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from webargs import ValidationError


def wsc_exception_handler(exc, context):
    # 先调用REST framework默认的异常处理方法获得标准错误响应对象,这里处理抛出的异常
    response = exception_handler(exc, context)
    if isinstance(exc, ValidationError):
        exc.status_code = 400
    if hasattr(exc, "status_code"):
        status_code = exc.status_code
    else:
        status_code = 500
    data = {"success": False}
    if status_code == 400:
        if exc.messages.get("query"):
            data["error_text"] = exc.messages.get("query")
        else:
            data["error_text"] = exc.messages.get("json")
        data["error_code"] = 400
        response = Response(data, status=status.HTTP_400_BAD_REQUEST)
    elif status_code == 404:
        data["error_text"] = "地址错误" if not exc.args else exc.args[0]
        data["error_code"] = 404
        response = Response(data, status=status.HTTP_404_NOT_FOUND)
    elif status_code == 401:
        data["error_text"] = exc.detail
        data["error_code"] = 401
        response = Response(data, status=status.HTTP_401_UNAUTHORIZED)
    elif status_code == 403:
        data["error_text"] = exc.detail
        data["error_code"] = 403
        response = Response(data, status=status.HTTP_403_FORBIDDEN)
    elif isinstance(exc, DatabaseError):
        data['error_text'] = exc.args[0]
        data["error_code"] = 507
        response = Response(data, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    elif isinstance(exc, TransactionManagementError):
        data['error_text'] = '服务器内部错误2'
        data["error_code"] = 507
        response = Response(data, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    else:
        data["error_text"] = "服务器错误, {detail}".format(detail=exc.args)
        data["error_code"] = 500
        response = Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response