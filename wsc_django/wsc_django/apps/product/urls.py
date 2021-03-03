"""
货品相关的路由
"""
from django.urls import path, re_path

from product import views


urlpatterns_admin = [
    path('admin/product/', views.AdminProductView.as_view()), # 货品创建&货品详情&编辑货品&批量删除货品
    path('admin/products/', views.AdminProductsView.as_view()), # 获取货品列表&批量修改货品(上架，下架)
    path('admin/product/groups/', views.AdminProductGroupsView.as_view()), # 批量更新货品分组
    path('admin/product/group/', views.AdminProductGroupView.as_view()), # 添加货品分组&编辑货品分组&删除货品分组&获取货品分组列表
    path('admin/product/group/sort/', views.AdminProductGroupSortView.as_view()), # 货品分组排序
    path('admin/product/sale_record/', views.AdminProductSaleRecordView.as_view()), # 获取一个货品的销售记录
]

urlpatterns_mall = [
    re_path(r'^mall/product/(?P<shop_code>\w+)/$', views.MallProductView.as_view()), # 获取单个货品详情
    re_path(r'^mall/products/(?P<shop_code>\w+)/$', views.MallProductsView.as_view()), # 获取所有货品列表,带上分组
]

urlpatterns = urlpatterns_admin + urlpatterns_mall


