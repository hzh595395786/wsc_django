import datetime

from webargs import fields, validate
from webargs.djangoparser import use_args

from delivery.serializers import AdminDeliveryConfigSerializer
from delivery.services import get_delivery_config_by_shop_id, update_delivery_config
from wsc_django.utils.views import AdminBaseView, MallBaseView


class AdminDeliveryConfigView(AdminBaseView):
    """后台-订单-获取配送设置"""

    def get(self, request):
        success, delivery_config = get_delivery_config_by_shop_id(self.current_shop.id)
        if not success:
            return self.send_fail(error_text=delivery_config)
        serializer = AdminDeliveryConfigSerializer(delivery_config)
        return self.send_success(data=serializer.data)


class AdminDeliveryConfigHomeView(AdminBaseView):
    """后台-订单-送货上门设置"""

    @use_args(
        {
            "home_minimum_order_amount": fields.Float(
                required=True, comment="配送模式起送金额"
            ),
            "home_delivery_amount": fields.Float(required=True, comment="配送模式配送费"),
            "home_minimum_free_amount": fields.Float(
                required=True, comment="配送模式免配送费最小金额"
            ),
        },
        location="json"
    )
    def put(self, request, args):
        import time
        t1 = time.time()
        success, msg = update_delivery_config(
            self.current_shop.id, args, self.current_user.id
        )
        if not success:
            return self.send_fail(error_text=msg)
        print(time.time()-t1)
        return self.send_success()


class AdminDeliveryConfigPickView(AdminBaseView):
    """后台-订单-自提设置"""

    # 参数校验
    def validate_time(self):
        try:
            datetime.datetime.strptime(self, "%H:%M")
        except Exception:
            return False
        return True

    @use_args(
        {
            "pick_service_amount": fields.Float(required=True, comment="自提模式服务费"),
            "pick_minimum_free_amount": fields.Float(
                required=True, comment="自提模式免服务费最小金额"
            ),
            "pick_today_on": fields.Boolean(required=True, comment="今天自提是否开启"),
            "pick_tomorrow_on": fields.Boolean(required=True, comment="明天自提是否开启"),
            "pick_periods": fields.Nested(
                {
                    "from_time": fields.String(
                        required=True, comment="自提起始时间", validate=validate_time
                    ),
                    "to_time": fields.String(
                        required=True, comment="自提终止时间", validate=validate_time
                    ),
                },
                many=True,
                validate=[validate.Length(1)],
                unknown=True,
                comment="自提时段",
            ),
        },
        location="json"
    )
    def put(self, request, args):
        success, msg = update_delivery_config(
            self.current_shop.id, args, self.current_user.id
        )
        if not success:
            return self.send_fail(error_text=msg)
        return self.send_success()


class AdminDeliveryConfigMethodView(AdminBaseView):
    """后台-订单-开启/关闭配送或者自提"""

    @use_args(
        {
            "home_on": fields.Boolean(comment="配送模式是否开启"),
            "pick_on": fields.Boolean(comment="自提模式是否开启"),
        },
        location="json"
    )
    def put(self, request, args):
        if not args:
            return self.send_fail(error_text="请选择配送设置项目")
        success, msg = update_delivery_config(self.current_shop.id, args)
        if not success:
            return self.send_fail(error_text=msg)
        return self.send_success()