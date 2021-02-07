from django.shortcuts import render
from rest_framework.generics import CreateAPIView

# Create your views here.
from user.serializers import MallCreateCheckSerializer


class MallCreateView(CreateAPIView):
    """商城-登录注册"""
    """
    注册登录省略
    """

    pass
