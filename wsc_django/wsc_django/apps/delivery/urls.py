"""
配送相关的路由
"""
from django.urls import path

from delivery import views


urlpatterns = [
    path('admin/delivery-config/', views.AdminDeliveryConfigView.as_view()),  # 后台获取配送配置
    path('admin/delivery-config/home/', views.AdminDeliveryConfigHomeView.as_view()),  # 送货上门设置
    path('admin/delivery-config/pick/', views.AdminDeliveryConfigPickView.as_view()),  # 自提设置
    path('admin/delivery-config/method/', views.AdminDeliveryConfigMethodView.as_view()),  # 开启/关闭配送或者自提
]
