"""项目要用到的一些类和函数"""
import datetime
import re

from django_redis import get_redis_connection
from rest_framework import serializers

from wsc_django.utils.region_file import REGION


ORDER_SHOP_TYPE_PREFIX = "60"  # 微商城系统店铺类型固定订单前缀


class FuncField(serializers.Field):
    """传入一个匿名函数，将该字段接收的值用函数转换"""

    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func

    def to_representation(self, value):
        return self.func(value)


class FormatAddress:

    region = REGION

    @classmethod
    def check_code(cls, code_list: list):
        """检查省市区编号合法性"""
        for code in code_list:
            if code not in REGION.keys():
                return False
        return True

    @classmethod
    def get_format_address(cls, province, city, county, address: str):
        """拼装省市区地址"""
        province_str = cls.get_region(province)
        city_str = cls.get_region(city)
        county_str = cls.get_region(county)

        ret = []
        for _ in [province_str, city_str, county_str]:
            # 北京, 北京市
            if _.rstrip("市") not in ret:
                ret.append(_)
        detail_address = "".join(ret)
        if detail_address not in address:
            address = detail_address + address
        return address

    @classmethod
    def get_region(cls, region):
        if isinstance(region, int):
            return cls.region.get(region, "")
        elif isinstance(region, str):
            if region.isdigit():
                return cls.region.get(int(region), "")
            else:
                return region
        return ""


class Emoji:
    """ Emoji表情 """

    @staticmethod
    def filter_emoji(keyword):
        keyword = re.compile(u"[\U00010000-\U0010ffff]").sub(u"", keyword)
        return keyword

    @staticmethod
    def check_emoji(keyword):
        reg_emoji = re.compile(u"[\U00010000-\U0010ffff]")
        has_emoji = re.search(reg_emoji, keyword)
        if has_emoji:
            return True
        else:
            return False


class NumGenerator:
    """ 单号生成器 """

    @staticmethod
    def generate(shop_id: int, order_type: int) -> str:
        """ 生成订单号，规则：店铺类型2位 + 店铺自增编号5位 + 订单日期6位 + 订单类型2位 + 订单自增编号4位

        :param order_type: 订单类型:  1:普通订单，5:拼团订单
        """
        today = datetime.date.today().strftime("%y%m%d")
        key = "num:{shop_id}:{order_type}:{today}".format(
            shop_id=shop_id, order_type=order_type, today=today
        )
        redis_conn = get_redis_connection("num_generate")
        num = redis_conn.incr(key)
        redis_conn.expire(key, 3600 * 24)
        result = "{shop_type}{shop_id_fill}{today}{order_type}{num_fill}".format(
            shop_type=ORDER_SHOP_TYPE_PREFIX,
            shop_id_fill=str(shop_id).zfill(5),
            today=today,
            order_type=str(order_type).zfill(2),
            num_fill=str(num).zfill(4),
        )
        return result

    @staticmethod
    def decode(num: str) -> tuple:
        """ 解码订单号

        :param num: 订单号码
        :return: 店铺id, 订单类型
        """
        shop_id = num[2:7]
        order_type = num[13:15]
        return (int(shop_id), order_type)


