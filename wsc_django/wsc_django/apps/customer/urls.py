"""
客户相关的路由
"""
from django.urls import path, re_path

from customer import views


urlpatterns_admin = [
    path('admin/customer/', views.AdminCustomerView.as_view()),  # 客户详情
    path('admin/customers/', views.AdminCustomersView.as_view()),  # 客户列表
    path('admin/customer/remark/', views.AdminCustomerRemarkView.as_view()),  # 修改客户备注
    path('admin/customer/points/', views.AdminCustomerPointsView.as_view()),  # 获取客户历史积分
    path('admin/customer/orders/', views.AdminCustomerOrdersView.as_view()),  # 获取客户历史订单
]

urlpatterns_mall = [
    re_path(r'^mall/mine/address/(?P<shop_code>\w+)/$', views.MallMineAddressView.as_view()),  # 添加送货地址&修改送货地址&删除送货地址&查询用的所有送货地址
    re_path(r'^mall/mine/default/address/(?P<shop_code>\w+)/$', views.MallMineDefaultAddressView.as_view()),  # 获取一个客户的默认地址
]

urlpatterns = urlpatterns_admin + urlpatterns_mall