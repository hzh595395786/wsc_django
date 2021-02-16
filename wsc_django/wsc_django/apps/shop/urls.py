"""
店铺相关的路由
"""
from django.urls import path
from shop import views

urlpatterns = [
    path('shop/', views.ShopView.as_view()), # 商铺创建和详情
    path('shops/', views.ShopListView.as_view()) # 商铺列表
]
