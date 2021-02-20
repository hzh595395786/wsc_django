"""
货品相关的路由
"""
from django.urls import path

from product import views


urlpatterns_admin = [
    path('admin/product/', views.ProductView.as_view()), # 货品创建&单个货品详情
]

urlpatterns_mall = [

]

urlpatterns = urlpatterns_admin + urlpatterns_mall


