import datetime

from webargs import fields, validate
from webargs.djangoparser import use_args

from product.constant import ProductStatus
from pvuv.interface import list_product_ids_by_shop_id_interface
from pvuv.serializers import ProductBrowseRecordsSerializer
from pvuv.services import list_product_browse_record_by_id, create_product_browse_record
from wsc_django.utils.arguments import StrToDict
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView, MallBaseView


_MAP_BROWSE_RECORD = {}


def register_browse_record(type):
    def register(func):
        _MAP_BROWSE_RECORD[type] = func
        return func

    return register


class AdminProductBrowseRecordsView(AdminBaseView):
    """后台-商品访问记录"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PRODUCT]
    )
    @use_args(
        {
            "product_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="货品ID"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop_id = self.current_shop.id
        args["to_date"] = datetime.date.today() + datetime.timedelta(1)
        args["from_date"] = datetime.date.today() - datetime.timedelta(7)
        record_list = list_product_browse_record_by_id(shop_id, **args)
        record_list = self._get_paginated_data(record_list, ProductBrowseRecordsSerializer)
        return self.send_success(data_list=record_list)


class MallBrowseRecord(MallBaseView):
    """商城-创建浏览记录"""

    @register_browse_record("product")
    def gen_product_browse_record(self, args: dict):
        product_id = int(args["spa_params"]["product_id"])
        product_ids = list_product_ids_by_shop_id_interface(
            self.current_shop.id, [ProductStatus.ON, ProductStatus.OFF]
        )
        if product_id not in product_ids:
            return False, "货品不存在"
        info = {
            "shop_id": self.current_shop.id,
            "user_id": self.current_user.id,
            "product_id": product_id,
            "start_time": args["start_time"],
            "duration": args["duration"],
            "pre_page_name": args["pre_page"].get("name"),
            "next_page_name": args["next_page"].get("name"),
        }
        create_product_browse_record(info)
        return True, None

    @use_args(
        {
            "fullpath": fields.String(
                required=True, validate=[validate.Length(1, 256)], comment="url全路径"
            ),
            "query": StrToDict(required=True, comment="路由里面的query参数"),
            "cur_page": StrToDict(required=True, comment="当前页面, 包含type, name2个值, str"),
            "pre_page": StrToDict(required=True, comment="上一个页面, 包含type, name2个值, str"),
            "next_page": StrToDict(required=True, comment="下一个页面, 包含type, name2个值, str"),
            "spa_query": StrToDict(required=True, comment="当前页面的一些参数"),
            "spa_params": StrToDict(required=True, comment="当前页面的一些参数"),
            "start_time": fields.DateTime(required=True, comment="进入当前页面的时间"),
            "duration": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="在页面停留的时间"
            ),
        },
        location="json"
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        # 暂时只记录商品的访问记录, 以后再扩展
        cur_page_type = args["cur_page"]["type"]
        gen_browse_record_func = _MAP_BROWSE_RECORD[cur_page_type]
        success, info = gen_browse_record_func(self, args)
        if not success:
            return self.send_fail(error_text=info)
        return self.send_success()