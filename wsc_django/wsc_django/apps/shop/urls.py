"""
店铺相关的路由
"""
from django.urls import path, re_path
from shop import views

urlpatterns_admin = [
    path('super/shop/', views.SuperShopView.as_view()), # 总后台-商铺创建和详情
    path('super/shops/', views.SuperShopListView.as_view()), # 总后台-商铺列表
    path('super/shop/status/', views.SuperShopStatusView.as_view()), # 总后台-通过shop_status获取所有商铺&修改商铺的shop_status
    path('super/shop/verify/', views.SuperShopVerifyView.as_view()), # 总后台-修改商铺的认证状态
    path('admin/shop/', views.AdminShopView.as_view()), # 商户后台-商铺详情

]

urlpatterns_mall = [
    re_path(r'^mall/shop/(?P<shop_code>\w+)/$', views.MallShopView.as_view()), # 商城端-全局获取店铺信息
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
