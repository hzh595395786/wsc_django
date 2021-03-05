"""
客户相关的路由
"""
from django.urls import path

from customer import views


urlpatterns_admin = [
    path('admin/customer/', views.AdminCustomerView.as_view()), # 客户详情
    path('admin/customers/', views.AdminCustomersView.as_view()), # 客户列表
    path('admin/customer/remark/', views.AdminCustomerRemarkView.as_view()), # 修改客户备注
    path('admin/customer/points/', views.AdminCustomerPointsView.as_view()), # 获取客户历史积分
]

urlpatterns_mall = [

]

urlpatterns = urlpatterns_admin + urlpatterns_mall