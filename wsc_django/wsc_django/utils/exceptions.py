"""异常处理"""
from django.db.utils import DatabaseError
from django.db.transaction import TransactionManagementError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def wsc_exception_handler(exc, context):
    # 先调用REST framework默认的异常处理方法获得标准错误响应对象
    response = exception_handler(exc, context)

    if isinstance(exc, DatabaseError):
        response = Response({'detail': '服务器内部错误1'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    if isinstance(exc, TransactionManagementError):
        response = Response({'detail': '服务器内部错误2'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

    return response