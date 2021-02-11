"""
员工相关的路由
"""
from django.urls import path
from staff import views


urlpatterns = [
    path('staff/', views.AdminStaffView.as_view()), # 员工的增删改查
    path('staff/apply/', views.StaffApplyView.as_view()), # 提交员工申请&获取申请信息
]
