"""
店铺设置相关路由
"""
from django.urls import path

from dashboard import views


urlpatterns = [
    path("admin/dashboard/shop/data/", views.AdminDashboardShopDataView.as_view()),  # 店铺数据概览
    path("admin/dashboard/order/data/", views.AdminDashboardOrderDataView.as_view()),  # 店铺订单数据
    path("admin/dashboard/product/data/", views.AdminDashboardProductDataView.as_view()),  # 店铺商品数据
]
