"""
访问记录相关的路由
"""
from django.urls import path, re_path

from pvuv import views

urlpatterns_admin =[
    path('api/admin/product/browse-records/', views.AdminProductBrowseRecordsView.as_view())  # 后台-商品访问记录
]

urlpatterns_mall = [
    re_path(r'api/mall/(?P<shop_code>\w+)/browse-record/$', views.MallBrowseRecord.as_view()),  # 商城生成访问记录
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
