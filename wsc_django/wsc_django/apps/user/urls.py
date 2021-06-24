"""
用户相关的路由
"""
from django.urls import path, re_path


from user import views

urlpatterns_admin = [
    path('api/super/user/authorization/', views.AdminUserAuthorizationView.as_view()),  # 总后台后台验证登录状态
    path('api/super/user/', views.SuperUserView.as_view()),  # 总后台获取用户详情&修改用户基本信息
    path('api/super/user/phone/', views.SuperUserPhoneView.as_view()),  # 总后台修改用户手机号
    path('api/super/user/password/', views.SuperUserPasswordView.as_view()),  # 总后台修改密码
    path('api/super/user/email/', views.SuperUserEmailView.as_view()),  # 总后台验证邮箱&b绑定邮箱&激活邮箱
    path('api/admin/user/', views.AdminUserView.as_view()),  # 后台用户登录注册
    path('api/admin/user/logout/', views.AdminUserLogoutView.as_view()),  # 后台退出登录
    path('api/admin/user/sms_code/', views.SMSCodeView.as_view()),  # 后台发送短信验证码
]

urlpatterns_mall = [
    re_path(r'^api/mall/(?P<shop_code>\w+)/user/$', views.MallUserView.as_view()),  # 商城端用户登录
    re_path(r'^api/mall/(?P<shop_code>\w+)/user/register/$', views.MallUserRegisterView.as_view()),  # 商城端用户注册
    re_path(r'^api/mall/(?P<shop_code>\w+)/user/authorization/$', views.MallUserAuthorizationView.as_view()),  # 商城端验证登录状态
    path('api/mall/sms_code/', views.SMSCodeView.as_view()),  # 商城端短信验证码
]

urlpatterns = urlpatterns_admin + urlpatterns_mall
