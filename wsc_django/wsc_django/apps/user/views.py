from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from user.serializers import MallUserSerializer
from wsc_django.utils.sms import gen_sms_code, YunPianSms, TencentSms


class MallUserView(APIView):
    """商城-登录注册"""

    # 测试使用，跳过登录,设置cookies
    def get(self, request):
        response = Response()
        res = response.set_cookie("wsc_shop_id", 1)
        print(res)
        return response


class MallSMSCodeView(APIView):
    """商城-短信验证接口"""

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
