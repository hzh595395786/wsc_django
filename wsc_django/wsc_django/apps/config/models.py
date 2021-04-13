from django.db import models

# Create your models here.
from shop.models import Shop
from wsc_django.utils.models import TimeBaseModel
from config.constant import (
    PrinterType,
    PrinterTemp,
    PrinterAutoPrint,
    PrinterStatus,
    ReceiptBrcodeActive,
)


class Printer(TimeBaseModel):
    """打印机模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="打印机对应店铺")
    type = models.SmallIntegerField(
        null=False,
        default=PrinterType.LOCAL,
        verbose_name="打印机类型1:本地2:云, 预留",
    )
    brand = models.SmallIntegerField(
        null=False,
        verbose_name="打印机品牌 1:易联云, 2:飞印, 3:佛山喜讯, 4:365 S1, 5:365 S2, 6:森果"
    )
    code = models.CharField(max_length=32, default="", verbose_name="打印机终端号")
    key = models.CharField(max_length=32, default="", verbose_name="打印机秘钥")
    temp_id = models.SmallIntegerField(
        null=False,
        default=PrinterTemp.ONE,
        verbose_name="打印模板, 预留",
    )
    auto_print = models.SmallIntegerField(
        null=False,
        default=PrinterAutoPrint.YES,
        verbose_name="订单自动打印",
    )
    status = models.SmallIntegerField(
        null=False,
        default=PrinterStatus.NORMAL,
        verbose_name="打印机状态,预留",
    )

    class Meta:
        db_table = "printer"
        verbose_name = "打印机"
        verbose_name_plural = verbose_name


class Receipt(TimeBaseModel):
    """小票模型类"""

    id = models.OneToOneField(
        Shop,
        primary_key=True,
        null=False,
        on_delete=models.CASCADE,
        verbose_name="一个店铺对应一个小票,就直接绑定"
    ).primary_key
    bottom_msg = models.CharField(max_length=128, null=False, default="", verbose_name="小票底部信息")
    bottom_qrcode = models.CharField(max_length=128, null=False, default="", verbose_name="小票底部二维码")
    bottom_image = models.CharField(max_length=512, null=False, default="", verbose_name="小票底部图片,预留")
    brcode_active = models.SmallIntegerField(
        null=False,
        default=ReceiptBrcodeActive.NO,
        verbose_name="打印订单号条码",
    )
    copies = models.SmallIntegerField(null=False, default=1, verbose_name="小票打印份数")

    class Meta:
        db_table = "receipt"
        verbose_name = "小票"
        verbose_name_plural = verbose_name


class MsgNotify(TimeBaseModel):
    """消息通知模型类"""

    id = models.OneToOneField(Shop, primary_key=True, null=False, on_delete=models.CASCADE).primary_key
    order_confirm_wx = models.BooleanField(null=False, default=False, verbose_name="开始配送/等待自提-微信")
    order_confirm_msg = models.BooleanField(null=False, default=False, verbose_name="开始配送/等待自提-短信")
    order_finish_wx = models.BooleanField(null=False, default=False, verbose_name="订单完成-微信")
    order_finish_msg = models.BooleanField(null=False, default=False, verbose_name="订单完成-短信")
    order_refund_wx = models.BooleanField(null=False, default=False, verbose_name="订单退款-微信")
    order_refund_msg = models.BooleanField(null=False, default=False, verbose_name="订单退款-短信")
    group_success_wx = models.BooleanField(null=False, default=False, verbose_name="成团提醒-微信")
    group_success_msg = models.BooleanField(null=False, default=False, verbose_name="成团提醒-短信")
    group_failed_wx = models.BooleanField(null=False, default=False, verbose_name="拼团失败-微信")
    group_failed_msg = models.BooleanField(null=False, default=False, verbose_name="拼团失败-短信")

    class Meta:
        db_table = "msgnotfiy"
        verbose_name = "消息通知"
        verbose_name_plural = verbose_name


class ShareSetup(TimeBaseModel):
    """分享设置模型类"""

    id = models.OneToOneField(Shop, primary_key=True, null=False, on_delete=models.CASCADE).primary_key
    custom_title_name = models.CharField(
        max_length=64, null=False, default="", verbose_name="自定义分享标题名称"
    )
    custom_share_description = models.CharField(
        max_length=64, null=False, default="", verbose_name="自定义分享描述"
    )

    class Meta:
        db_table = "share_setup"
        verbose_name = "分享设置"
        verbose_name_plural = verbose_name


class SomeConfig(TimeBaseModel):
    """一些杂乱的配置项,和店铺绑定的"""

    id = models.OneToOneField(Shop, primary_key=True, null=False, on_delete=models.CASCADE).primary_key
    show_off_product = models.BooleanField(null=False, default=True, verbose_name="货品板块显示已下架货品")
    new_order_voice = models.BooleanField(null=False, default=True, verbose_name="新订单语音提醒")
    weixin_jsapi = models.BooleanField(null=False, default=False, verbose_name="是否开启微信支付")
    on_delivery = models.BooleanField(null=False, default=True, verbose_name="是否开启货到付款")

    class Meta:
        db_table = "some_config"
        verbose_name = "一些杂乱的配置项"
        verbose_name_plural = verbose_name
