"""
店铺相关的路由
"""
from django.urls import path
from shop import views

urlpatterns = [
    path('shop', views.ShopCreateView.as_view())
]
