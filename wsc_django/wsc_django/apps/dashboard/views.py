from webargs import fields, validate
from webargs.djangoparser import use_args

from dashboard.constant import StatisticType
from dashboard.services import list_shop_dashboard_data, list_order_dashboard_data, list_product_dashboard_data
from wsc_django.utils.core import TimeFunc
from wsc_django.utils.views import AdminBaseView


class AdminDashboardShopDataView(AdminBaseView):
    """后台-店铺数据概览"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_DASHBORD]
    )
    @use_args(
        {
            "statistic_type": fields.Integer(
                required=True,
                validate=validate.OneOf(
                    [StatisticType.DAILY, StatisticType.MONTHLY, StatisticType.YEARLY]
                ),
            ),
            "from_date": fields.String(missing="", comment="筛选起始日期"),
            "to_date": fields.String(missing="", comment="筛选终止日期"),
        },
        location="query"
    )
    def get(self, request, args):
        try:
            from_date, to_date = TimeFunc.get_to_date_by_from_date(
                args["from_date"], args["to_date"], args["statistic_type"]
            )
        except ValueError as e:
            return self.send_fail(error_text=str(e))
        _, data_list = list_shop_dashboard_data(
            self.current_shop.id,
            from_date,
            to_date,
            args["statistic_type"],
        )
        return self.send_success(data_list=data_list)


class AdminDashboardOrderDataView(AdminBaseView):
    """后台-店铺数据-订单数据"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_DASHBORD]
    )
    @use_args(
        {
            "statistic_type": fields.Integer(
                required=True,
                validate=validate.OneOf(
                    [StatisticType.DAILY, StatisticType.MONTHLY, StatisticType.YEARLY]
                ),
            ),
            "from_date": fields.String(missing="", comment="筛选起始日期"),
            "to_date": fields.String(missing="", comment="筛选终止日期"),
        },
        location="query"
    )
    def get(self, request, args):
        try:
            from_date, to_date = TimeFunc.get_to_date_by_from_date(
                args["from_date"], args["to_date"], args["statistic_type"]
            )
        except ValueError as e:
            return self.send_fail(error_text=str(e))
        _, data_list = list_order_dashboard_data(
            self.current_shop.id,
            from_date,
            to_date,
            args["statistic_type"],
        )
        return self.send_success(data_list=data_list)


class AdminDashboardProductDataView(AdminBaseView):
    """后台-店铺数据-商品数据"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_DASHBORD]
    )
    @use_args(
        {
            "statistic_type": fields.Integer(
                required=True,
                validate=validate.OneOf(
                    [StatisticType.DAILY, StatisticType.MONTHLY, StatisticType.YEARLY]
                ),
            ),
            "from_date": fields.String(missing="", comment="筛选起始日期"),
            "to_date": fields.String(missing="", comment="筛选终止日期"),
        },
        location="query"
    )
    def get(self, request, args):
        try:
            from_date, to_date = TimeFunc.get_to_date_by_from_date(
                args["from_date"], args["to_date"], args["statistic_type"]
            )
        except ValueError as e:
            return self.send_fail(error_text=str(e))
        _, data_list = list_product_dashboard_data(
            self.current_shop.id, from_date, to_date
        )
        return self.send_success(data_list=data_list)

