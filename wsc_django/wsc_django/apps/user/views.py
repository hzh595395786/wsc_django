from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from wechatpy.oauth import WeChatOAuth

from customer.services import create_customer
from user.utils import jwt_response_payload_handler
from wsc_django.settings.dev import MP_APPSECRET, MP_APPID
from wsc_django.utils.sms import gen_sms_code, YunPianSms, TencentSms
from wsc_django.utils.views import UserBaseView, MallBaseView
from user.serializers import UserCreateSerializer
from user.interface import get_customer_by_user_id_and_shop_id_interface
from user.services import (
    get_user_by_wx_unionid,
    get_openid_by_user_and_appid,
    create_user_openid,
)


class AdminUserView(UserBaseView):
    """后台-用户-登录注册"""

    def get(self, request):
        return Response()


class MallUserView(MallBaseView):
    """商城-用户-登录注册"""

    def post(self, request, shop_code):
        code = request.data.get("code", None)
        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        shop_appid = MP_APPID
        shop_appsecret = MP_APPSECRET
        wechat_oauth = WeChatOAuth(
            app_id=shop_appid,
            secret=shop_appsecret,
            redirect_uri="",
            scope="snsapi_userinfo",
        )
        try:
            wechat_oauth.fetch_access_token(code)
            user_info = wechat_oauth.get_user_info()
        except:
            return self.send_fail(error_text='获取微信授权失败')
        """
           user_info = {
                   "openid": "oMZbfv3iy12L1q1XGWpkko_P_YPI",
                   "nickname": "hpf",
                   "sex": 1,
                   "language": "zh_CN",
                   "city": "武汉",
                   "province": "湖北",
                   "country": "中国",
                   "headimgurl": "http://thirdwx.qlogo.cn/mmopen/vi_32/yctGCWkz1jI2ybfVe12KmrXIb9R89dfgnoribX9sG75hBPJQlsK30fnib9r4nKELHcpcXAibztiaHH3jz65f03ibOlg/132",
                   "privilege": [],
                   "unionid": "oIWUauOLaT50pWKUeNKhKP6W0WIU"
               }
        """
        user_info["headimgurl"] = user_info["headimgurl"].replace("http://", "https://")
        user = get_user_by_wx_unionid(user_info.get("unionid"))
        if not user:
            new_user_info = {
                "phone": user_info.get('phone'),
                "sex": user_info.get('sex'),
                "nickname": user_info.get("nickname"),
                "realname": user_info.get("realname"),
                "head_image_url": user_info.get("headimgurl"),
                "wx_unionid": user_info.get("unionid"),
                "wx_openid": user_info.get("openid"),
                "wx_country": user_info.get("country"),
                "wx_province": user_info.get("province"),
                "wx_city": user_info.get("city"),
            }
            user_serializer = UserCreateSerializer(data=new_user_info)
            user_serializer.save()
            user = request.user
        ret, user_openid = get_openid_by_user_and_appid(user.id, shop_appid)
        # 不存在则添加用户的openid
        if not ret:
            info = {
                'user_id': user.id,
                'mp_appid': shop_appid,
                'wx_openid': user_info.get("openid"),
            }
            create_user_openid(info)
        customer = get_customer_by_user_id_and_shop_id_interface(user.id, shop.id)
        # 新客户则创建客户信息
        if not customer:
            create_customer(user.id, shop.id)
        token = self._set_current_user(user)
        response_data = jwt_response_payload_handler(token, user, request)
        return self.send_success(data=response_data)


class MallSMSCodeView(APIView):
    """商城-用户-短信验证接口"""

    def post(self, request, mobile):
        if self.request.META.get('HTTP_X_FORWARDED_FOR'):
            remote_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            remote_ip = self.request.META.get("REMOTE_ADDR")
        user_id = self.request.user.id
        use_ip = "bind_phone_ip:%s:%s" % (user_id, remote_ip)
        redis_conn =get_redis_connection("verify_codes")
        if redis_conn.get(use_ip):
            return JsonResponse({'success':False, 'error_text':'一分钟只能发生一次'})
        sms_code = gen_sms_code()
        print("sms_code: ", sms_code)  # 测试用

        # 在发送短信验证码前保存数据，以免多次访问和注册时验证
        pl = redis_conn.pipeline()
        pl.setex("sms_%s_%s" % (user_id, mobile), 300, sms_code) # 验证码过期时间300秒
        pl.setex(use_ip, 60, 1) # 验证码60秒发送一次
        pl.execute()
        # # 调用第三方接口发送短信
        # use = "绑定手机号"
        # # 先用云片发,失败就用腾讯发
        # ret, info = YunPianSms.send_yunpian_verify_code(mobile, sms_code, use)
        # if not ret:
        #     ret, info = TencentSms.send_tencent_verify_code(mobile, sms_code, use)
        # if not ret:
        #     return JsonResponse({'success':False, "error_text": info})

        return JsonResponse({'success':True})
