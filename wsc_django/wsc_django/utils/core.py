"""项目要用到的一些类和函数"""
import datetime
import re

import requests
from django_redis import get_redis_connection
from rest_framework import serializers

from settings import BAIDU_APIKEY, BAIDU_SECRETKEY
from wsc_django.utils.region_file import REGION


ORDER_SHOP_TYPE_PREFIX = "60"  # 微商城系统店铺类型固定订单前缀


class FuncField(serializers.Field):
    """传入一个匿名函数，将该字段接收的值用函数转换"""

    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func

    def to_representation(self, value):
        """read时调用"""
        return self.func(value)

    def to_internal_value(self, data):
        """write时调用，必须重写"""
        return data


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


class TimeFunc:
    @staticmethod
    def get_to_date_by_from_date(from_date, to_date, statistic_type):
        """根据选择的日期，月份，年份获取起止区间
        """
        if statistic_type not in [1, 3, 4]:
            raise ValueError("统计类型不受支持")
        try:
            if statistic_type == 1:
                from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d")
                if to_date:
                    to_date = datetime.datetime.strptime(
                        to_date, "%Y-%m-%d"
                    ) + datetime.timedelta(days=1)
                else:
                    to_date = from_date + datetime.timedelta(days=1)
            elif statistic_type == 3:
                from_date = datetime.datetime.strptime(from_date, "%Y-%m")
                to_date = datetime.datetime.strptime(to_date, "%Y-%m")
                if to_date.month + 1 > 12:
                    month = 1
                    year = to_date.year + 1
                else:
                    year = to_date.year
                    month = to_date.month + 1
                to_date = datetime.datetime(year=year, month=month, day=1)
            elif statistic_type == 4:
                # 按年现在不进行筛选，给个默认所有的日期
                from_date = datetime.datetime(year=2015, month=1, day=1)
                to_date = datetime.datetime(year=2100, month=1, day=1)
        except ValueError:
            raise ValueError("日期格式传入错误，请检查")
        return from_date, to_date


class Baidu:
    @staticmethod
    def get_baidu_token():
        """获取access_token，先从redis中取，取不到则重新生成"""
        redis_conn = get_redis_connection("default")
        access_token = redis_conn.get("wsc_baidu_token")
        if access_token:
            return access_token.decode("utf-8")

        url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}".format(
            BAIDU_APIKEY, BAIDU_SECRETKEY
        )
        data = requests.get(
            url,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            verify=False,
        ).json()
        access_token = data.get("access_token", "")
        if access_token:
            redis_conn.setex("wsc_baidu_token", 60 * 60 * 24 * 10, access_token)
        return access_token


