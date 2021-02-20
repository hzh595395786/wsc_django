"""
员工相关的路由
"""
from django.urls import path, re_path
from staff import views


urlpatterns = [
    path(r'staff/', views.AdminStaffView.as_view()), # 员工的增删改查
    re_path(r'^staff/apply/(?P<shop_code>\w+)/$', views.StaffApplyView.as_view()), # 提交员工申请&获取申请信息
]


