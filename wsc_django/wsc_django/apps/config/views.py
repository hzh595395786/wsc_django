import json
import random
import re
import string
import time
import qiniu
import requests

from django_redis import get_redis_connection
from sts.sts import Sts
from webargs.djangoparser import use_args
from webargs import fields, validate
from wechatpy import WeChatClient

from config.constant import PrinterBrand
from wsc_django.utils.views import GlobalBaseView, AdminBaseView
from config.serializers import ShareSetupSerializer, PrinterSerializer, ReceiptSerializer, MsgNotifySerializer
from logs.constant import ConfigLogType
from shop.constant import ShopVerifyActive, ShopPayActive
from shop.serializers import AdminShopSerializer
from wsc_django.apps.settings import (
    MP_APPID, MP_APPSECRET,
    QINIU_ACCESS_KEY,
    QINIU_SECRET_KEY,
    QINIU_BUCKET_SHOP_IMG,
    TENCENT_COS_SECRETID,
    TENCENT_COS_SECRETKEY,
)
from config.services import (
    create_share_setup,
    update_share_setup,
    get_share_setup_by_id,
    get_receipt_by_shop_id,
    get_printer_by_shop_id,
    list_msg_notify_fields,
    get_msg_notify_by_shop_id,
    update_msg_notify_by_shop_id,
    update_some_config_by_shop_id,
    create_printer_by_shop_id, update_receipt_by_shop_id,
)
from config.interface import (
    update_shop_data_interface,
    create_config_log_interface,
    get_staff_by_user_id_and_shop_id_with_user_interface,
)


msg_notify_field_list = list_msg_notify_fields()


class AdminConfigShopInfoView(AdminBaseView):
    """后台-设置-店铺信息获取"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    def get(self, request):
        shop = self.current_shop
        staff = get_staff_by_user_id_and_shop_id_with_user_interface(
            shop.super_admin_id, shop.id
        )
        shop.create_user = staff
        shop_info = AdminShopSerializer(shop).data
        return self.send_success(data=shop_info)


class AdminConfigPrintInfoView(AdminBaseView):
    """后台-设置-打印设置信息获取"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    def get(self, request):
        shop_id = self.current_shop.id
        printer = get_printer_by_shop_id(shop_id)
        receipt = get_receipt_by_shop_id(shop_id)
        printer_info = PrinterSerializer(printer).data
        receipt_info = ReceiptSerializer(receipt).data
        return self.send_success(printer_data=printer_info, receipt_data=receipt_info)


class AdminConfigMsgNotifyView(AdminBaseView):
    """后台-设置-消息通知-获取&修改店铺消息通知设置"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    def get(self, request):
        shop_id = self.current_shop.id
        msg_notify = get_msg_notify_by_shop_id(shop_id)
        msg_notify = MsgNotifySerializer(msg_notify).data
        return self.send_success(data=msg_notify)

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "field": fields.String(
                required=True,
                validate=[validate.OneOf(msg_notify_field_list)],
                comment="更改的字段",
            ),
            "value": fields.Boolean(required=True, comment="更改的值"),
        },
        location="json"
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        msg_notify_info = {args.get("field"): args.get("value")}
        update_msg_notify_by_shop_id(shop_id, msg_notify_info)
        return self.send_success()


class AdminConfigShopImgView(AdminBaseView):
    """后台-设置-店铺信息-修改店铺logo"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "shop_img": fields.String(
                required=True, validate=[validate.Length(1, 128)], comment="店铺logo"
            )
        },
        location="json",
    )
    def put(self, request, args):
        shop = self.current_shop
        update_shop_data_interface(shop, args)
        return self.send_success()


class AdminConfigShopNameView(AdminBaseView):
    """后台-设置-店铺信息-修改店铺名"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "shop_name": fields.String(
                required=True, validate=[validate.Length(1, 300)], comment="店铺名"
            )
        },
        location="json",
    )
    def put(self, request, args):
        shop = self.current_shop
        shop = update_shop_data_interface(shop, args)
        # 记录日志
        log_info = {
            "shop_id": shop.id,
            "operator_id": self.current_user.id,
            "operate_type": ConfigLogType.SHOP_NAME,
            "operate_content": shop.shop_name,
        }
        create_config_log_interface(log_info)
        return self.send_success()


class AdminConfigShopPhoneView(AdminBaseView):
    """后台-设置-店铺信息-修改店铺联系电话"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {"shop_phone": fields.String(required=True, comment="店铺名")}, location="json"
    )
    def put(self, request, args):
        shop = self.current_shop
        shop = update_shop_data_interface(shop, args)
        # 记录日志
        log_info = {
            "shop_id": shop.id,
            "operator_id": self.current_user.id,
            "operate_type": ConfigLogType.SHOP_PHONE,
            "operate_content": shop.shop_phone,
        }
        create_config_log_interface(log_info)
        return self.send_success()


class AdminConfigShopAddressView(AdminBaseView):
    """后台-设置-店铺信息-更改店铺地址"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "shop_province": fields.Integer(required=True, comment="省份编号"),
            "shop_city": fields.Integer(required=True, comment="城市编号"),
            "shop_county": fields.Integer(required=True, comment="区份编号"),
            "shop_address": fields.String(
                required=True, validate=[validate.Length(0, 100)], comment="详细地址"
            ),
        },
        location="json"
    )
    def put(self, request, args):
        shop = self.current_shop
        update_shop_data_interface(shop, args)
        return self.send_success()


class AdminConfigPrinterView(AdminBaseView):
    """后台-设置-打印设置-修改打印机"""

    def validate_feiyin(self, code):
        """飞印打印机验证终端号是否存在"""
        _headers = {
            "Cookie": "__utmt=1; sessionid=d2e9cb1cd2c64639f4e18019d35343ee; username=; usertype=1; account=7502; key=e506eb41e1c43558a6abd7618321b6aa; __utma=240375839.1986845255.1436857060.1437040538.1437050867.4; __utmb=240375839.5.10.1437050867; __utmc=240375839; __utmz=240375839.1436857060.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
            "Host": "my.feyin.net",
            "Referer": "http://my.feyin.net/crm/accountIndex",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36",
            "Connection": "keep-alive",
        }
        _data = {
            "deviceCode": code,
            "installAddress": "",
            "simCode": "",
            "groupname": "",
        }
        _r = requests.post(
            "http://my.feyin.net/activeDevice",
            data=_data,
            headers=_headers,
            timeout=(1, 5),
        )
        content = _r.content.decode("utf-8")
        pattern = re.compile("终端编号不存在", re.S)
        result = re.search(pattern, content)
        return result

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "brand": fields.Integer(
                required=True,
                validate=[
                    validate.OneOf(
                        [
                            PrinterBrand.YILIANYUN,
                            # PrinterBrand.FEIYIN,
                            # PrinterBrand.FOSHANXIXUN,
                            # PrinterBrand.S1,
                            # PrinterBrand.S2,
                            # PrinterBrand.SENGUO,
                        ]
                    )
                ],
                comment="打印机品牌/型号",
            ),
            "code": fields.String(
                required=True, validate=[validate.Length(0, 32)], comment="打印机终端号"
            ),
            "key": fields.String(
                required=False,
                missing="",
                validate=[validate.Length(0, 32)],
                comment="打印机秘钥",
            ),
            "auto_print": fields.Boolean(required=True, comment="订单自动打印"),
        },
        location="json",
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        args["auto_print"] = int(args.get("auto_print", 1))
        if args.get("brand") == PrinterBrand.FEIYIN:
            ret = None
            try:
                ret = self.validate_feiyin(args.get("code"))
            except:
                # 留着以后记录日志
                pass
            if ret:
                return self.send_fail(error_text="终端号不存在")
        printer = create_printer_by_shop_id(shop_id, args)
        # 记录日志
        log_info = {
            "shop_id": shop_id,
            "operator_id": self.current_user.id,
            "operate_type": ConfigLogType.PRINTER_SET,
            "operate_content": "型号：{}，终端号：{}".format(printer.brand_text, printer.code),
        }
        create_config_log_interface(log_info)
        return self.send_success(printer_id=printer.id)


class AdminConfigReceiptBottomMsgView(AdminBaseView):
    """后台-设置-小票设置-小票底部信息设置"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "bottom_msg": fields.String(
                required=True, validate=[validate.Length(0, 128)], comment="小票底部信息"
            )
        },
        location="json"
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        update_receipt_by_shop_id(shop_id, args)
        return self.send_success()


class AdminConfigReceiptBottomQrcodeView(AdminBaseView):
    """后台-设置-小票设置-小票底部二维码设置"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "bottom_qrcode": fields.String(
                required=True, validate=[validate.Length(0, 128)], comment="小票底部二维码"
            )
        },
        location="json"
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        update_receipt_by_shop_id(shop_id, args)
        return self.send_success()


class AdminConfigReceiptBrcodeActiveView(AdminBaseView):
    """后台-设置-小票设置-打印订单号条码"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {"brcode_active": fields.Boolean(required=True, comment="打印单号条码")}, location="json"
    )
    def put(self, request, args):
        args["brcode_active"] = int(args.get("brcode_active", 1))
        shop_id = self.current_shop.id
        update_receipt_by_shop_id(shop_id, args)
        return self.send_success()


class AdminConfigReceiptCopiesView(AdminBaseView):
    """后台-设置-小票设置-小票底部信息设置"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "copies": fields.Integer(
                required=True, validate=[validate.Range(0, 5)], comment="默认打印份数"
            )
        },
        location="json"
    )
    def put(self, request, args):
        args["brcode_active"] = int(args.get("brcode_active", 1))
        shop_id = self.current_shop.id
        update_receipt_by_shop_id(shop_id, args)
        return self.send_success()


class AdminPayModeConfigView(AdminBaseView):
    """后台-商铺的支付方式设置"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "key": fields.String(
                required=True,
                validate=[validate.OneOf(["weixin_jsapi", "on_delivery"])],
                comment="设置的字段名",
            ),
            "value": fields.Boolean(required=True, comment="设置的字段值"),
        },
        location="json"
    )
    def put(self, request, args):
        shop = self.current_shop
        config_info = {args.get("key"): args.get("value")}
        is_wx = "weixin_jsapi" in config_info.keys()
        # 未认证或者未开通线上支付时，还是可以点击关闭货到付款按钮
        if is_wx and shop.cerify_active != ShopVerifyActive.YES:
            return self.send_fail(
                error_text="已认证的商铺才可申请开通在线支付，您的店铺暂未认证，请前往认证"
            )
        if is_wx and shop.pay_active != ShopPayActive.YES:
            return self.send_fail(error_text="店铺未开通线上支付")
        some_config = update_some_config_by_shop_id(shop.id, config_info)
        # 最少需要保留一种支付方式
        if not some_config.weixin_jsapi and not some_config.on_delivery:
            return self.send_fail(error_text="至少保留一种商城支付方式，否则客户无法支付")
        return self.send_success()


class AdminSomeConfigView(AdminBaseView):
    """后台-一些奇怪的店铺设置"""

    @use_args(
        {
            "key": fields.String(
                required=True,
                validate=[validate.OneOf(["show_off_product", "new_order_voice"])],
                comment="设置的字段名",
            ),
            "value": fields.Boolean(required=True, comment="设置的字段值"),
        },
        location="json"
    )
    def put(self, request, args):
        shop = self.current_shop
        config_info = {args.get("key"): args.get("value")}
        update_some_config_by_shop_id(shop.id, config_info)
        return self.send_success()


class AdminConfigShopSetupView(AdminBaseView):
    """后台-获取商铺常规设置信息"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    def get(self, request):
        shop = self.current_shop
        share_setup = get_share_setup_by_id(shop.id)
        if not share_setup:
            share_setup = create_share_setup(shop.id, shop.shop_name)
        share_setup_data = ShareSetupSerializer(share_setup).data
        return self.send_success(data=share_setup_data)


class AdminConfigCustomTitleNameView(AdminBaseView):
    """后台-修改店铺分享信息中的自定义标题名称"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "custom_title_name": fields.String(
                required=True, validate=[validate.Length(1, 30)], comment="自定义分享标题名称"
            )
        },
        location="json"
    )
    def put(self, request,args):
        shop = self.current_shop
        update_share_setup(shop.id, args)
        return self.send_success()


class AdminConfigCustomShareDescriptionView(AdminBaseView):
    """后台-修改店铺分享信息中的自定义分享描述"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CONFIG]
    )
    @use_args(
        {
            "custom_share_description": fields.String(
                required=True, validate=[validate.Length(1, 45)], comment="自定义分享描述"
            )
        },
        location="json"
    )
    def put(self, request,args):
        shop = self.current_shop
        update_share_setup(shop.id, args)
        return self.send_success()


class WechatJsapiSigntureView(GlobalBaseView):
    """商城-获取微信jsapi"""

    @use_args({"url": fields.String(required=True, comment="当前页面的URL")}, location="query")
    def get(self, request, args):
        redis_conn = get_redis_connection("default")
        access_token = redis_conn.get("access_token")
        access_token = access_token.decode("utf-8") if access_token else None
        wechat_client = WeChatClient(
            appid=MP_APPID, secret=MP_APPSECRET, access_token=access_token, timeout=5
        )
        if not access_token:
            access_token = wechat_client.fetch_access_token()
            redis_conn.setex("access_token", 3600, access_token.get("access_token"))
        jsapi_ticket = redis_conn.get("jsapi_ticket")
        jsapi_ticket = jsapi_ticket.decode("utf-8") if jsapi_ticket else None
        if not jsapi_ticket:
            jsapi_ticket = wechat_client.jsapi.get_jsapi_ticket()
            redis_conn.setex("jsapi_ticket", 7100, jsapi_ticket)
        noncestr = "".join(random.sample(string.ascii_letters + string.digits, 10))
        timestamp = int(time.time())
        signature = wechat_client.jsapi.get_jsapi_signature(
            noncestr, jsapi_ticket, timestamp, args.get("url")
        )
        data = {
            "appID": MP_APPID,
            "timestamp": timestamp,
            "nonceStr": noncestr,
            "signature": signature,
        }

        return self.send_success(data=data)


class QiniuImgTokenView(GlobalBaseView):
    """后台-获取七牛token"""

    def get(self, request):
        q = qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
        token = q.upload_token(QINIU_BUCKET_SHOP_IMG, expires=60 * 30)
        return self.send_success(token=token)


class TencentCOSCredential(GlobalBaseView):
    """商城端-腾讯云COS临时凭证"""

    def get(self, request):
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            # 域名，非必须，默认为 sts.tencentcloudapi.com
            'domain': 'sts.tencentcloudapi.com',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 1800,
            'secret_id': TENCENT_COS_SECRETID,
            # 固定密钥
            'secret_key': TENCENT_COS_SECRETKEY ,
            # 设置网络代理
            # 'proxy': {
            #     'http': 'xx',
            #     'https': 'xx'
            # },
            # 换成你的 bucket
            'bucket': 'zhihao-1300126182',
            # 换成 bucket 所在地区
            'region': 'ap-nanjing',
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': '*',
            # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
            'allow_actions': [
                # 简单上传
                'name/cos:PutObject',
                'name/cos:PostObject',
            ],

        }
        response = {}
        try:
            sts = Sts(config)
            response = sts.get_credential()
            print('get data : ' + json.dumps(dict(response), indent=4))
        except Exception as e:
            print(e)
        return self.send_success(data=response)
