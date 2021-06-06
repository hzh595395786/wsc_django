"""
货品相关的路由
"""
from django.urls import path, re_path

from product import views


urlpatterns_admin = [
    path('api/admin/product/', views.AdminProductView.as_view()),  # 货品创建&货品详情&编辑货品
    path('api/admin/products/', views.AdminProductsView.as_view()),  # 获取货品列表&批量修改货品(上架，下架)&批量删除货品
    path('api/admin/product/groups/', views.AdminProductGroupsView.as_view()),  # 批量更新货品分组&获取货品分组列表
    path('api/admin/product/group/', views.AdminProductGroupView.as_view()),  # 添加货品分组&编辑货品分组&删除货品分组
    path('api/admin/product/group/sort/', views.AdminProductGroupSortView.as_view()),  # 货品分组排序
    path('api/admin/product/sale_records/', views.AdminProductSaleRecordView.as_view()),  # 获取一个货品的销售记录
    path(
        'api/admin/product/alive-groupon/', views.AdminProductAliveGrouponView.as_view()
    ),  # 查询此刻或者未来有拼团活动的货品
]

urlpatterns_mall = [
    re_path(r'^api/mall/product/(?P<shop_code>\w+)/$', views.MallProductView.as_view()),  # 获取单个货品详情
    re_path(r'^api/mall/products/(?P<shop_code>\w+)/$', views.MallProductsView.as_view()),  # 获取所有货品列表,带上分组
]

urlpatterns = urlpatterns_admin + urlpatterns_mall


