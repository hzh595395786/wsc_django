import urllib.parse
import json

from django.shortcuts import redirect
from rest_framework.response import Response
from webargs import fields
from webargs.djangoparser import use_args

from payment.interface import get_user_openid_interface, create_user_openid_interface, pay_order_interfaces
from payment.service import get_openid_redirect_url, handle_lcsw_callback
from wsc_django.utils.views import MallBaseView, GlobalBaseView


class MallPaymentOpenIdView(MallBaseView):
    """商城获取支付的open_id"""

    @use_args(
        {
            "redirect_uri": fields.String(
                required=True, comment="获取公众号配置重定向的前端路由，前端传递的是**需要跳转到的页面**的前端路由"
            )
        },
        location="query"
    )
    def get(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        success, user_openid = get_user_openid_interface(
           self.current_user.id, "lcwx-{}".format(self.current_shop.id)
        )
        if success:
            return self.send_success(wx_openid=user_openid.wx_openid)
        success, redirect_url = get_openid_redirect_url(
            self.current_shop,
            urllib.parse.quote(args["redirect_uri"], safe=""),
        )
        if not success:
            return self.send_fail(error_text=redirect_url)
        return self.send_fail(error_text="获取openid失败", error_redirect=redirect_url)


class MallOpenidLcswView(MallBaseView):
    """利楚商务openid接口"""

    @use_args(
        {
            "openid": fields.String(required=True, comment="利楚返回的openid"),
            "redirect": fields.String(
                required=True, comment="openid处理完成后的重定向页面"
            ),
        },
        location="query"
    )
    def get(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        mp_appid = "lcwx-{}".format(self.current_shop.id)
        success, user_openid = get_user_openid_interface(
            self.current_user.id, mp_appid
        )
        if success:
            user_openid.set_wx_openid(args["openid"])
        else:
            create_user_openid_interface(
                self.current_user.id, mp_appid, args["openid"]
            )
        return redirect(urllib.parse.unquote(args["redirect"]))


class LcswPaymentCallbackView(GlobalBaseView):
    """利楚支付回调"""

    def post(self, request):
        """ 回调传入参数举例

        {"attach":"SENGUOPRODUCT","channel_trade_no":"4000082001201707140681458896","end_time":"20170714105108",
          "key_sign":"fce359fd0dd87d7d52d374de7be40657","merchant_name":"贵港市港北区优鲜果品经营部","merchant_no":"862500210000002",
          "out_trade_no":"101947210121317071410510301546","pay_type":"010","receipt_fee":"1","result_code":"01","return_code":"01",
          "return_msg":"支付成功","terminal_id":"10194721","terminal_time":"20170714105103","terminal_trace":"c1992000206",
          "total_fee":"1","user_id":"ojUElxOZlqPRYdXnOOzzVoKToTR0"}
        响应码：01成功 ，02失败，响应码仅代表通信状态，不代表业务结果
        """
        res_text = request.data.decode(encoding="utf-8")
        res_dict = json.loads(res_text)
        # TODO: 日志点
        _, order = handle_lcsw_callback(res_dict)
        pay_order_interfaces(order)
        # 订单提交成功微信提醒, 暂时只有普通订单才发送消息,且页面没有控制按钮
        # todo 待写
        ret_dict = {"return_code": "01", "return_msg": "success"}
        return Response(data=ret_dict)