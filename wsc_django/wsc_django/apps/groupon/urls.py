"""
店铺设置相关路由
"""
from django.urls import path, re_path

from groupon import views


urlpatterns_admin = [
    path('api/admin/groupon/', views.AdminGrouponView.as_view()),  # 创建拼团&编辑拼团&拼团活动详情
    path(
        'api/admin/groupon/period/verification/', views.AdminGrouponPeriodVerificationView.as_view()
    ),  # 验证拼团时间合法性
    path('api/admin/groupon/off/', views.AdminGrouponOffView.as_view()),  # 停用拼团
    path('api/admin/groupons/', views.AdminGrouponsView.as_view()),  # 拼团活动列表页
    path('api/admin/groupon-attends/', views.AdminGrouponAttendsView.as_view()),  # 拼团参与列表
    path('api/admin/groupon-attend/', views.AdminGrouponAttendView.as_view()),  # 拼团参与详情
    path(
        'api/admin/gruopon-attend/orders/', views.AdminGrouponAttendOrdersView.as_view()
    ),  # 后台获取一个团的所有参团订单
    path(
        'api/admin/groupon-attend/success/force/', views.AdminGrouponAttendSuccessForceView.as_view()
    ),  # 强制成团
]

urlpatterns_mall = [
    re_path(
        r'api/mall/(?P<shop_code>\w+)/groupon-attend/initation/', views.MallGrouponAttendInitationView.as_view()
    ),  # 开团
]

urlpatterns = urlpatterns_mall + urlpatterns_admin