import datetime

from django.utils.timezone import make_aware
from webargs.djangoparser import use_args
from webargs import fields, validate

from logs.constant import OrderLogType
from logs.interface import list_operator_by_shop_id_with_user_interface
from logs.serializers import (
    OrderLogSerializer,
    OperatorSerializer,
    ConfigLogSerializer,
    ProductLogSerializer,
    PromotionLogSerializer,
)
from wsc_django.utils.arguments import StrToList
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView
from logs.services import (
    get_all_module_dict,
    list_one_module_log_by_filter,
    dict_more_modules_log_by_filter,
)


all_module_dict = get_all_module_dict()


class AdminLogsView(AdminBaseView):
    """后台-员工-操作日志"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_STAFF]
    )
    @use_args(
        {
            "operator_ids": fields.Function(
                deserialize=lambda x: x.replace(" ", "").split(","),
                missing=[],
                comment="操作人ID",
            ),
            "operate_module_ids": StrToList(
                missing=[],
                validate=[validate.ContainsOnly(list(all_module_dict.values()))],
                comment="模块ID",
            ),
        },
        location="query"
    )
    def get(self, request, args):
        args["operate_module_ids"] = [int(_) for _ in args.get("operate_module_ids")]
        # django时区问题
        args["end_date"] = make_aware(datetime.datetime.today() + datetime.timedelta(1))
        args["from_date"] = make_aware(datetime.datetime.today() - datetime.timedelta(90))
        shop_id = self.current_shop.id
        # 查询单个还是多个
        operate_module_ids = args.pop("operate_module_ids")
        # 查单个
        if len(operate_module_ids) == 1:
            module_id = operate_module_ids[0]
            log_list = list_one_module_log_by_filter(
                shop_id, module_id, **args
            )
            module_id_2_log_list = {module_id: log_list}
        # 查询多个
        else:
            module_id_2_log_list = dict_more_modules_log_by_filter(
                shop_id, operate_module_ids, **args
            )
        """
        module_2_log_list = {
            1: [log, log ...],
            2: [log, log ...],
            ...
        }
        """
        # 封装数据
        module_id_2_name = {v: k.lower() for k, v in all_module_dict.items()}
        all_log_list = []
        for module_id, log_list_query in module_id_2_log_list.items():
            def_name = "format_{}_data".format(module_id_2_name.get(module_id))
            log_list = getattr(self, def_name)(log_list_query)
            all_log_list.extend(log_list)

        all_log_list = sorted(
            all_log_list, key=lambda x: x["operate_time"], reverse=True
        )
        return self.send_success(data_list=all_log_list)

    def format_order_data(self, log_list_query):
        """封装订单日志数据"""
        for log in log_list_query:
            if log.operate_type in [
                OrderLogType.HOME_DELIVERY_AMOUNT,
                OrderLogType.HOME_MINIMUM_FREE_AMOUNT,
                OrderLogType.HOME_MINIMUM_ORDER_AMOUNT,
                OrderLogType.PICK_MINIMUM_FREE_AMOUNT,
                OrderLogType.PICK_SERVICE_AMOUNT,
            ]:
                log.old_value = log.operate_content.split("|")[0]
                log.new_value = log.operate_content.split("|")[1]
                log.operate_content = ""
        order_log_serializer = OrderLogSerializer(log_list_query, many=True)
        log_list = order_log_serializer.data
        return log_list

    def format_config_data(self, log_list_query):
        """封装设置日志数据"""
        log_list = ConfigLogSerializer(log_list_query, many=True).data
        return log_list

    def format_product_data(self, log_list_query):
        """封装货品日志数据"""
        log_list = ProductLogSerializer(log_list_query, many=True).data
        return log_list

    def format_promotion_data(self, log_list_query):
        """封装货品日志数据"""
        log_list = PromotionLogSerializer(log_list_query, many=True).data
        return log_list


class AdminOperatorsView(AdminBaseView):
    """后台-员工-操作记录-操作人员获取"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_STAFF]
    )
    def get(self, request):
        shop_id = self.current_shop.id
        operator_list = list_operator_by_shop_id_with_user_interface(shop_id)
        operator_list = self._get_paginated_data(operator_list, OperatorSerializer)
        return self.send_success(data_list=operator_list)
