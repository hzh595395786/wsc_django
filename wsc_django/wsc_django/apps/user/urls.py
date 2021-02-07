"""
用户相关的路由
"""
from django.conf.urls import url
from user import views

urlpatterns = [
    url(r'^mall/$', views.MallCreateView.as_view()), # 商城注册登录
]
