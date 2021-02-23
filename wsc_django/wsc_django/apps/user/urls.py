"""
用户相关的路由
"""
from django.urls import path, re_path
from user import views

urlpatterns_admin = [
    path('admin/user/', views.AdminUserView.as_view()), # 后台用户登录注册
]

urlpatterns_mall = [
    re_path(r'^mall/user/(?P<shop_code>\w+)/$', views.MallUserView.as_view()), # 商城端用户注册登录
    re_path(r'^mall/sms_code/(?P<mobile>1[3-9]\d{9})/$', views.MallSMSCodeView.as_view()), # 商城端短信验证
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
