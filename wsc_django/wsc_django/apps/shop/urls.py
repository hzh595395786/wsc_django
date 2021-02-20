"""
店铺相关的路由
"""
from django.urls import path
from shop import views

urlpatterns_admin = [
    path('admin/shop/', views.ShopView.as_view()), # 商铺创建和详情
    path('admin/shops/', views.ShopListView.as_view()) # 商铺列表
]

urlpatterns_mall = [

]

urlpatterns = urlpatterns_admin + urlpatterns_mall
