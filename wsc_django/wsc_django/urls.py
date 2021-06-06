"""wsc_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter

urlpatterns = [
    # path(r'^admin/$', admin.site.urls),
    path(r'', include('config.urls')),
    path(r'', include('customer.urls')),
    path(r'', include('dashboard.urls')),
    path(r'', include('delivery.urls')),
    path(r'', include('demo.urls')),
    path(r'', include('groupon.urls')),
    path(r'', include('logs.urls')),
    path(r'', include('order.urls')),
    path(r'', include('payment.urls')),
    path(r'', include('printer.urls')),
    path(r'', include('product.urls')),
    path(r'', include('promotion.urls')),
    path(r'', include('pvuv.urls')),
    path(r'', include('shop.urls')),
    path(r'', include('staff.urls')),
    path(r'', include('storage.urls')),
    path(r'', include('user.urls')),
    path(r'', include('ws.urls')),
]

# 自带的API web
router = DefaultRouter()
urlpatterns += router.urls


