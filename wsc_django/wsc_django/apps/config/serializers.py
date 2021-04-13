from rest_framework import serializers


class ShareSetupSerializer(serializers.Serializer):
    """店铺分享序列化器类"""

    custom_title_name = serializers.CharField(label="自定义分享标题名称")
    custom_share_description = serializers.CharField(label="自定义分享描述")


class SomeConfigSerializer(serializers.Serializer):
    """店铺的一些奇怪的开关设置"""

    new_order_voice = serializers.BooleanField(label="新订单语音提醒")
    show_off_product  = serializers.BooleanField(label="显示已下架货品")
    weixin_jsapi = serializers.BooleanField(label="是否开通微信支付")
    on_delivery = serializers.BooleanField(label="是否开通货到付款")


class PrinterSerializer(serializers.Serializer):
    """打印机序列化器类"""

    brand = serializers.IntegerField(label="打印机品牌")
    code = serializers.CharField(label="打印机终端号")
    key = serializers.CharField(label="打印机秘钥")
    auto_print = serializers.BooleanField(label="是否订单自动打印")


class ReceiptSerializer(serializers.Serializer):
    """小票序列化器类"""

    bottom_msg = serializers.CharField(label="小票底部附加文字")
    bottom_qrcode = serializers.CharField(label="小票底部附加二维码")
    brcode_active = serializers.BooleanField(label="是否打印订单号条码")
    copies = serializers.IntegerField(label="默认打印份数")


class MsgNotifySerializer(serializers.Serializer):
    """消息通知序列化器类"""

    order_confirm_wx = serializers.BooleanField(label="开始配送/等待自提-微信")
    order_confirm_msg = serializers.BooleanField(label="开始配送/等待自提-短信")
    order_finish_wx = serializers.BooleanField(label="订单完成-微信")
    order_finish_msg = serializers.BooleanField(label="订单完成-短信")
    order_refund_wx = serializers.BooleanField(label="订单退款-微信")
    order_refund_msg = serializers.BooleanField(label="订单退款-短信")
    group_success_wx = serializers.BooleanField(label="成团提醒-微信")
    group_success_msg = serializers.BooleanField(label="成团提醒-短信")
    group_failed_wx = serializers.BooleanField(label="拼团失败-微信")
    group_failed_msg = serializers.BooleanField(label="拼团失败-短信")