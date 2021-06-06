"""
店铺设置相关路由
"""
from django.urls import path

from dashboard import views


urlpatterns = [
    path("api/admin/dashboard/shop/data/", views.AdminDashboardShopDataView.as_view()),  # 店铺数据概览
    path("api/admin/dashboard/order/data/", views.AdminDashboardOrderDataView.as_view()),  # 店铺订单数据
    path("api/admin/dashboard/product/data/", views.AdminDashboardProductDataView.as_view()),  # 店铺商品数据
]
