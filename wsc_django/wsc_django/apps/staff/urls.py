"""
员工相关的路由
"""
from django.urls import path, re_path
from staff import views


urlpatterns = [
    re_path(r'^staff/apply/(?P<shop_code>\w+)/$', views.StaffApplyView.as_view()),  # 提交员工申请&获取申请信息
    path('admin/staff/', views.AdminStaffView.as_view()),  # 员工详情&编辑员工&删除员工
    path('admin/staff/apply/', views.AdminStaffApplyView.as_view()),  # 员工申请列表&通过员工申请
    path('admin/staffs/', views.AdminStaffListView.as_view()),  # 员工列表
]


