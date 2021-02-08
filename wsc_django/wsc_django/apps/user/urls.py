"""
用户相关的路由
"""
from django.urls import path
from user import views

urlpatterns = [
    path(r'mall/', views.MallCreateView.as_view()), # 商城注册登录
]
