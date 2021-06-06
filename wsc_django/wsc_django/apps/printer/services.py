import datetime
import hashlib
import time

import requests
import jinja2
from django.utils.timezone import make_aware

from config.services import get_receipt_by_shop_id, get_printer_by_shop_id
from logs.constant import OrderLogType
from logs.services import create_order_log
from order.models import Order
from shop.services import get_shop_by_shop_id


ORDER_TPL_58 = (
    "<FS><center>{{shop.shop_name}}</center></FS>"
    + "订单号: {{order.num}}\n"
    + "{% if receipt_config.brcode_active %}<BR3>{{order.num}}</BR3>{% endif %}"
    + "下单时间: {{order.create_time}}\n"
    + "打印时间: {{print_time}}\n"
    + "**************商品**************\n"
    + "<table>"
    + "<tr>"
    + "<td>商品名</td>"
    + "<td>单价</td>"
    + "<td>数量</td>"
    + "<td>小计</td>"
    + "</tr>"
    + "{% for order_line in order.order_lines %}"
    + "<tr>"
    + "<td>{{order_line.product_name}}</td>"
    + "<td>{{order_line.price_net | round(2)}}</td>"
    + "<td>{{order_line.quantity_net | round(2)}}</td>"
    + "<td>{{order_line.amount_net | round(2)}}</td>"
    + "</tr>"
    + "{% endfor %}"
    + "</table>"
    + "********************************"
    + "<right>{{order.delivery_amount_text}}: {{order.delivery_amount_net | round(2)}}</right>"
    + "<FS><right>合计：{{order.total_amount_net | round(2)}}元</right></FS>"
    + "<right>{{order.pay_type_text}}</right>\n"
    + "********************************"
    + "<FS>客户: {{order.address.name}} {% if order.address.sex %}{{order.address.sex_text}}{% endif %}</FS>\n"
    + "<FS>电话: {{order.address.phone}}</FS>\n"
    + "{% if order.delivery_method == 1 %}<FS>地址: {{ order.address.full_address }}</FS>\n{% endif %}"
    + "{% if order.remark %}<FS>备注: {{order.remark}}</FS>\n{% endif %}"
    + "********************************"
    + "{% if receipt_config.bottom_msg %}{{receipt_config.bottom_msg}}\n{% endif %}"
    + "{% if receipt_config.bottom_qrcode %}<QR>{{receipt_config.bottom_qrcode}}</QR>{% endif %}"
    + "<center>技术支持: 森果 senguo.cc</center>"
)


class ylyPrinter:
    """易联云打印机"""

    def send_request(self, data, copy):
        """ 发送打印请求

        :param data: 打印体
        :param copy: 打印份数
        """
        if not data:
            return False, "易联云打印失败，请在店铺设置中检查打印机终端号是否正确设置"
        try:
            for _ in range(1, copy + 1):
                r = requests.post(
                    "http://open.10ss.net:8888", data=data, timeout=(1, 5)
                )
            text = int(eval(r.text)["state"])
        except:
            return False, "易联云打印接口返回异常，请稍后重试"
        if text == 1:
            return True, ""
        elif text in [3, 4]:
            return False, "易联云打印失败，请在店铺设置中检查打印机终端号是否正确设置"
        else:
            return False, "易联云打印失败，错误代码：%s"%text


def print_order(order: Order, user_id: int = 0):
    """
    订单打印
    :param order:
    :param user_id:
    :return:
    """
    shop_id = order.shop.id
    shop = get_shop_by_shop_id(shop_id)
    receipt_config = get_receipt_by_shop_id(shop_id)
    printer = ylyPrinter()
    template = jinja2.Template(ORDER_TPL_58)
    body = template.render(
        order=order,
        print_time=make_aware(datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
        shop=shop,
        receipt_config=receipt_config,
    )
    printer_config = get_printer_by_shop_id(shop_id)
    if not printer_config:
        return False, "请先添加打印机"
    partner = "1693"  # 用户ID
    apikey = "664466347d04d1089a3d373ac3b6d985af65d78e"  # API密钥
    timenow = str(int(time.time()))  # 当前时间戳
    machine_code = printer_config.code  # 打印机终端号 520
    mkey = printer_config.key  # 打印机密钥 110110
    if machine_code and mkey:
        sign = "{}machine_code{}partner{}time{}{}".format(
            apikey, machine_code, partner, timenow, mkey
        )
        sign = hashlib.md5(sign.encode("utf-8")).hexdigest().upper()
    else:
        return False, "打印机配置错误"
    data = {
        "partner": partner,
        "machine_code": machine_code,
        "content": body,
        "time": timenow,
        "sign": sign,
    }
    success, msg = printer.send_request(data, receipt_config.copies)
    if success and user_id >= 0:
        log_info = {
            "order_num": order.order_num,
            "shop_id": order.shop.id,
            "operator_id": user_id,
            "operate_type": OrderLogType.PRINT,
        }
        create_order_log(log_info)
    return success, msg