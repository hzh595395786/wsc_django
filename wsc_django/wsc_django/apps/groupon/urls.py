"""
店铺设置相关路由
"""
from django.urls import path

from groupon import views


urlpatterns_admin = [
    path('admin/groupon/', views.AdminGrouponView.as_view()),  # 创建拼团&编辑拼团&拼团活动详情获取
]

urlpatterns_mall = [
]

urlpatterns = urlpatterns_mall + urlpatterns_admin