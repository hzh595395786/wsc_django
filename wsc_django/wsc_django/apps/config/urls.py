"""
店铺设置相关路由
"""
from django.urls import path

from config import views


urlpatterns = [
    path('admin/config/shop-info/', views.AdminConfigShopInfoView.as_view()),  # 店铺信息获取
    path('admin/config/print-info/', views.AdminConfigPrintInfoView.as_view()),  # 打印信息获取
    path('admin/config/msg-notify/', views.AdminConfigMsgNotifyView.as_view()),  # 获取消息通知设置&设置消息通知
    path('admin/config/shop/img/', views.AdminConfigShopImgView.as_view()),  # 修改店铺logo
    path('admin/config/shop/name/', views.AdminConfigShopNameView.as_view()),  # 修改店铺名
    path('admin/config/shop/phone/', views.AdminConfigShopPhoneView.as_view()),  # 修改店铺联系方式
    path('admin/config/shop/address/', views.AdminConfigShopAddressView.as_view()),  # 修改店铺地址
    path('admin/config/printer/', views.AdminConfigPrinterView.as_view()),  # 修改打印机设置
    path(
        'admin/config/receipt/bottom-msg/', views.AdminConfigReceiptBottomMsgView.as_view()
    ),  # 小票底部信息设置
    path(
        'admin/config/receipt/bottom-qrcode/', views.AdminConfigReceiptBottomQrcodeView.as_view()
    ),  # 小票底部二维码设置
    path(
        'admin/config/receipt/brcode-active/', views.AdminConfigReceiptBrcodeActiveView.as_view()
    ),  # 打印订单号条码
    path(
        'admin/config/receipt/copies/', views.AdminConfigReceiptCopiesView.as_view()
    ),  # 打印订单号条码
    path(
        'admin/shop/pay-mode-config/', views.AdminPayModeConfigView.as_view()
    ),  # 店铺支付方式设置按钮
    path('admin/shop/some-config/', views.AdminSomeConfigView.as_view()),  # 店铺的一些奇怪设置按钮
    path('admin/config/shop-setup/', views.AdminConfigShopSetupView.as_view()),  # 获取店铺常规设置信息
    path(
        'admin/config/custom-title-name/', views.AdminConfigCustomTitleNameView.as_view()
    ),  # 修改店铺分享信息中的自定义标题名称
    path(
        'admin/config/custom-share-description/', views.AdminConfigCustomShareDescriptionView.as_view()
    ),  # 修改店铺分享信息中的自定义分享描述
    path('config/wechat/jsapi-signature/', views.WechatJsapiSigntureView.as_view()),  # 获取微信jsapi
    path('qiniu/img-token/', views.QiniuImgTokenView.as_view()),  # 获取七牛的上传照片token
]
