"""
订单相关的路由
"""
from django.urls import path, re_path

from order import views


urlpatterns_admin = [
    path('api/admin/orders/', views.AdminOrdersView.as_view()),  # 后台获取订单列表
    path('api/admin/order/', views.AdminOrderView.as_view()),  # 后台获取订单详情
    path('api/admin/order/print/', views.AdminOrderPrintView.as_view()),  # 后台打印订单
    path('api/admin/order/confirm/', views.AdminOrderConfirmView.as_view()),  # 后台确认订单
    path('api/admin/order/direct/', views.AdminOrderDirectView.as_view()),  # 后台一键完成订单
    path('api/admin/order/finish/', views.AdminOrderFinishView.as_view()),  # 后台完成订单
    path('api/admin/order/refund/', views.AdminOrderRefundView.as_view()),  # 后台订单退款
    path('api/admin/order/operate-log/', views.AdminOrderOperateLogView.as_view()),  # 后台获取订单日志
    path('api/admin/order/paid/count/', views.AdminOrderPaidCountView.as_view()),  # 未处理订单数
    path('api/admin/abnormal-order/count/', views.AdminAbnormalOrderCountView.as_view()),  # 获取异常订单数量
    path('api/admin/abnormal-orders/', views.AdminAbnormalOrdersView.as_view()),  # 后台获取异常订单列表
]

urlpatterns_mall = [
    re_path(r'^api/mall/(?P<shop_code>\w+)/order/$', views.MallOrderView.as_view()),  # 提交订单&订单详情
    re_path(r'^api/mall/(?P<shop_code>\w+)/order/cart/verify/$', views.MallCartVerifyView.as_view()),  # 购物篮内验证
    re_path(r'^api/mall/(?P<shop_code>\w+)/order/product/verify/$', views.MallProductVerifyView.as_view()),  # 确认订单前验证
    re_path(r'^api/mall/(?P<shop_code>\w+)/orders/', views.MallOrdersView.as_view()),  # 商城获取客户订单列表
    path('api/mall/order/cancellation/', views.MallOrderCancellationView.as_view()),  # 商城订单取消
    path('api/mall/order/payment/', views.MallOrderPaymentView.as_view()),  # 商城订单支付
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
