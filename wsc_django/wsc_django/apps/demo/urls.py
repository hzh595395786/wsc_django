"""
店铺设置相关路由
"""
from django.urls import path

from demo import views


urlpatterns = [
    path('demo/', views.DemoView.as_view())  # 测试接口
]
