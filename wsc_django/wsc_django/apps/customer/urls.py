"""
客户相关的路由
"""
from django.urls import path

from customer import views


urlpatterns_admin = [
    path('admin/customer/', views.AdminCustomerView.as_view()), # 客户详情
]

urlpatterns_mall = [

]

urlpatterns = urlpatterns_admin + urlpatterns_mall