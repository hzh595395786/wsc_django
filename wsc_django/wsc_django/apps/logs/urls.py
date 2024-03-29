"""
操作日志相关的路由
"""
from django.urls import path

from logs import views


urlpatterns = [
    path('api/admin/logs/', views.AdminLogsView.as_view()),  # 操作记录列表获取
    path('api/admin/log/operators/', views.AdminOperatorsView.as_view()),  # 操作人员列表获取
]
