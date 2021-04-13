from webargs import fields, validate
from webargs.djangoparser import use_args

from groupon.constant import GrouponType
from groupon.interface import publish_gruopon_interface, expire_groupon_interface
from groupon.services import create_groupon
from wsc_django.utils.views import AdminBaseView


class AdminGrouponView(AdminBaseView):
    """后台-拼团-创建拼团&编辑拼团&拼团活动详情获取"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "product_id": fields.Integer(required=True, comment="商品id"),
            "price": fields.Decimal(required=True, comment="拼团价"),
            "from_datetime": fields.DateTime(required=True, comment="拼团活动开始时间"),
            "to_datetime": fields.DateTime(required=True, comment="拼团活动结束时间"),
            "groupon_type": fields.Integer(
                required=True,
                validate=[validate.OneOf([GrouponType.NORMAL, GrouponType.MENTOR])],
                comment="拼团活动类型 1:普通 2:老带新",
            ),
            "success_size": fields.Integer(
                required=True, validate=[validate.Range(2, 50)], comment="成团人数"
            ),
            "quantity_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="购买数量上限"
            ),
            "success_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="成团数量上限"
            ),
            "attend_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="参团数量上限"
            ),
            "success_valid_hour": fields.Integer(
                required=True, validate=[validate.OneOf([24, 48])], comment="开团有效时间"
            ),
        },
        location="json"
    )
    def post(self, request, args):
        success, groupon = create_groupon(
            self.current_shop.id, self.current_user.id, args
        )
        if not success:
            return self.send_fail(error_text=groupon)
        publish_gruopon_interface(groupon)
        expire_groupon_interface(groupon)
        return self.send_success()

