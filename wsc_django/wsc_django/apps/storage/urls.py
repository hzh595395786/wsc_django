"""
库存相关的路由
"""
from django.urls import path

from storage import views


urlpatterns = [
    path('api/admin/product/storage-records/', views.AdminProductStorageRecordsView.as_view()),  # 获取货品库存变更记录
]
