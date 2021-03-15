"""
店铺设置相关路由
"""
from django.urls import path

from config import views


urlpatterns = [
    path('config/wechat/jsapi-signature/', views.WechatJsapiSigntureView.as_view()), # 获取微信jsapi
]
