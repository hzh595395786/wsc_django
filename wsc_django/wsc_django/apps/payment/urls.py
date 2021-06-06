"""
支付相关的路由
"""
from django.urls import path, re_path

from payment import views


urlpatterns = [
    re_path(r'^api/mall/(?P<shop_code>\w+)/payment/openid/$', views.MallPaymentOpenIdView.as_view()),  # 获取支付的openid
    re_path(r'^api/mall/(?P<shop_code>\w+)/openid/lcsw/$', views.MallOpenidLcswView.as_view()),  # 利楚openid接口
    path('api/payment/lcsw/callback/order/', views.LcswPaymentCallbackView.as_view()),  # 利楚商务回调
]
