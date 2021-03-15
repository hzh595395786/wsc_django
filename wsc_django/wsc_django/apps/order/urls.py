"""
订单相关的路由
"""
from django.urls import path, re_path

from order import views


urlpatterns_admin = [

]

urlpatterns_mall = [
    re_path(r'^mall/(?P<shop_code>\w+)/order/$', views.MallOrderView.as_view()), # 提交订单&订单详情
    re_path(r'^mall/(?P<shop_code>\w+)/order/cart/verify/$', views.MallCartVerifyView.as_view()), # 购物篮内验证
    re_path(r'^mall/(?P<shop_code>\w+)/order/product/verify/$', views.MallProductVerifyView.as_view()), # 确认订单前验证
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
