from rest_framework import status
from django_redis import get_redis_connection
from webargs.djangoparser import use_args
from webargs import fields, validate
from wechatpy.oauth import WeChatOAuth

from customer.services import create_customer
from user.constant import UserLoginType, Sex
from user.models import User
from user.utils import jwt_response_payload_handler, ZhiHaoJWTAuthentication
from wsc_django.utils.arguments import DecryptPassword
from wsc_django.apps.settings import MP_APPSECRET, MP_APPID
from wsc_django.utils.constant import PHONE_RE, PASSWORD_RE, EMAIL_RE
from wsc_django.utils.sms import gen_sms_code, YunPianSms, TencentSms
from wsc_django.utils.views import UserBaseView, MallBaseView, AdminBaseView, GlobalBaseView, SuperBaseView
from user.serializers import UserCreateSerializer, SuperUserSerializer, EmailSerializer, UserSerializer
from user.interface import (
    get_customer_by_user_id_and_shop_id_interface,
    get_customer_by_user_id_and_shop_code_interface,
)
from user.services import (
    get_user_by_wx_unionid,
    get_openid_by_user_id_and_appid,
    create_user_openid,
    get_user_by_phone,
    get_user_by_phone_and_password,
    update_user_basic_data,
    update_user_phone, validate_sms_code, update_user_password, send_email, get_user_by_email
)


class AdminUserAuthorizationView(SuperBaseView):
    """总后台-用户登录认证"""

    @use_args(
        {
            "token": fields.String(required=True, allow_none=True, comment="token值"),
            "refresh_token": fields.String(required=True, allow_none=True, comment="refresh_token值"),
            "shop_code": fields.String(required=False, comment="商铺编号，若从小程序端调用则必传")
        }
    )
    def post(self, request, args):
        jwt = ZhiHaoJWTAuthentication()
        res, user = jwt.authenticate_token(args.get("token"))
        if not res:
            refresh_res, user = jwt.authenticate_token(args.get("refresh_token"))
            if refresh_res:
                # 若token过期，而refresh_token未过期，则刷新token，返回已过期且带上token和用户信息
                token = self._refresh_current_user(user)
                serializer = SuperUserSerializer(user)
                return self.send_success(data={'expire': True, 'token': token, 'user_data': serializer.data})
            else:
                # 若token过期，且refresh_token也过期，则返回401
                return self.send_error(
                    status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
                )
        else:
            # 若token未到期返回未过期，不带token, 带上用户信息
            serializer = SuperUserSerializer(user)
            shop_code = args.get("shop_code", None)
            user_data = dict(serializer.data)
            if shop_code:
                # 额外查询用户的积分数据
                customer = get_customer_by_user_id_and_shop_code_interface(user.id, shop_code)
                user_data["points"] = round(float(customer.point), 2) if customer else 0
                user_data["is_new_customer"] = (
                    customer.is_new_customer() if customer else True
                )
            return self.send_success(data={'expire': False, 'user_data': user_data})


class SuperUserView(SuperBaseView):
    """总后台-用户-获取用户详情&修改用户基本信息"""

    @use_args(
        {
            "sign": fields.String(required=True, comment="加密认证"),
            "timestamp": fields.Integer(required=True, comment="时间戳"),
            "user_id": fields.Integer(required=True, comment="用户ID"),
        },
        location="query"
    )
    @SuperBaseView.validate_sign("sign", ("user_id", "timestamp"))
    def get(self, request, args):
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        serializer = SuperUserSerializer(user)
        return self.send_success(data=serializer.data)

    @use_args(
        {
            "sign": fields.String(required=True, comment="加密认证"),
            "timestamp": fields.Integer(required=True, comment="时间戳"),
            "user_id": fields.Integer(required=True, comment="用户ID"),
            "nickname": fields.String(required=False, validate=[validate.Length(1, 15)], comment="用户昵称"),
            "realname": fields.String(required=False, validate=[validate.Length(1, 15)], comment="用户真实姓名"),
            "sex": fields.Integer(
                required=False,
                validate=[validate.OneOf([Sex.UNKNOWN, Sex.FEMALE, Sex.MALE])],
            ),
            "birthday": fields.Date(required=False, comment="出生日期"),
            "head_image_url": fields.String(required=False, validate=[validate.Length(0,1024)], comment="用户头像")
        }
    )
    @SuperBaseView.validate_sign("sign", ("user_id", "timestamp"))
    def put(self, request, args):
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        if not args:
            return self.send_fail(error_text="参数有误")
        user = update_user_basic_data(user, args)
        serializer = UserSerializer(user)
        return self.send_success(data=serializer.data)


class SuperUserPhoneView(SuperBaseView):
    """总后台-用户-修改用户手机号"""

    @use_args(
        {
            "sign": fields.String(required=True, comment="加密认证"),
            "timestamp": fields.Integer(required=True, comment="时间戳"),
            "user_id": fields.Integer(required=True, comment="用户ID"),
            "phone": fields.String(required=True, validate=[validate.Regexp(PHONE_RE)], comment="手机号"),
            "sms_code": fields.String(required=True, comment="短信验证码"),
        },
        location="json"
    )
    @SuperBaseView.validate_sign("sign", ("user_id", "timestamp"))
    def put(self, request, args):
        user = self._get_current_user(request)
        phone = args["phone"]
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        # 短信验证码校验
        success, info = validate_sms_code(phone, args["sms_code"])
        if not success:
            return self.send_fail(error_text=info)
        success, info = update_user_phone(user, phone)
        if not success:
            return self.send_fail(error_text=info)
        return self.send_success()


class SuperUserPasswordView(SuperBaseView):
    """总后台-用户-修改密码"""

    @use_args(
        {
            "sign": fields.String(required=True, comment="加密认证"),
            "timestamp": fields.Integer(required=True, comment="时间戳"),
            "user_id": fields.Integer(required=True, comment="用户ID"),
            "phone": fields.String(required=True, validate=[validate.Regexp(PHONE_RE)], comment="手机号"),
            "sms_code": fields.String(required=True, comment="短信验证码"),
            "password1": DecryptPassword(required=True, validate=[validate.Regexp(PASSWORD_RE)], comment="密码"),
            "password2": DecryptPassword(required=True, validate=[validate.Regexp(PASSWORD_RE)], comment="重复密码"),
        }
    )
    @SuperBaseView.validate_sign("sign", ("user_id", "timestamp"))
    def put(self, request, args):
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        phone = args["phone"]
        # 短信验证码校验
        success, info = validate_sms_code(phone, args["sms_code"])
        if not success:
            return self.send_fail(error_text=info)
        success, info = update_user_password(user, args["password1"] ,args["password2"])
        if not success:
            return self.send_fail(error_text=info)
        token, refresh_token = self._set_current_user(user)
        response_data = jwt_response_payload_handler(token, refresh_token, user, request)
        return self.send_success(data=response_data)


class SuperUserEmailView(SuperBaseView):
    """总后台-用户-验证邮箱&b绑定邮箱&激活邮箱"""

    @use_args(
        {
            "sign": fields.String(required=True, comment="加密认证"),
            "timestamp": fields.Integer(required=True, comment="时间戳"),
            "user_id": fields.Integer(required=True, comment="用户ID"),
            "token": fields.String(required=True, comment="验证token"),
        },
        location="query"
    )
    @SuperBaseView.validate_sign("sign", ("user_id", "timestamp"))
    def get(self, request, args):
        token = args["token"]
        # 验证token
        user = User.check_verify_email_token(token)
        if user is None:
            return self.send_error(
                status_code=status.HTTP_400_BAD_REQUEST, error_message={"detail": "链接信息无效"}
            )
        else:
            user.email_active = True
            user.save()
            return self.send_success()

    @use_args(
        {
            "email": fields.String(required=True, validate=[validate.Regexp(EMAIL_RE)], comment="邮箱")
        }
        , location="json"
    )
    def put(self, request, args):
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        check_user = get_user_by_email(args["email"])
        if check_user:
            return self.send_fail(error_text="该邮箱已绑定其他用户")
        serializer = EmailSerializer(user, data=args)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.send_success()

    @use_args(
        {
            "email": fields.String(required=True, validate=[validate.Regexp(EMAIL_RE)], comment="邮箱")
        }
        , location="json"
    )
    def post(self, request, args):
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"error_text": "用户未登录"}
            )
        success, info = send_email(user, args["email"])
        if not success:
            return self.send_fail(error_text=info)
        return self.send_success()




class AdminUserView(UserBaseView):
    """后台-用户-登录注册"""
    # 父类进行了登录验证，这里覆盖掉
    authentication_classes = ()

    @use_args(
        {
            "code": fields.String(required=False, comment="微信code"),
            "phone": fields.String(required=False, validate=[validate.Regexp(PHONE_RE)], comment="手机号"),
            "sms_code": fields.String(required=False, comment="短信验证码"),
            "password": DecryptPassword(required=False, validate=[validate.Regexp(PASSWORD_RE)], comment="密码"),
            "login_type": fields.Integer(
                required=True,
                validate=[validate.OneOf(
                    [UserLoginType.WX, UserLoginType.PWD, UserLoginType.PHONE]
                )],
                comment="登录方式,0:微信，1：密码，2：手机"
            )
        },
        location="json",
    )
    def post(self, request, args):
        login_type = args["login_type"]
        code = args.get("code", None)
        phone = args.get("phone", None)
        pwd = args.get("password", None)
        sms_code = args.get("sms_code", None)
        # 若登录方式为微信
        if login_type == UserLoginType.WX:
            if not code:
                return self.send_fail(error_text="微信登录缺少code")
        # 若登录方式为密码
        elif login_type == UserLoginType.PWD:
            if not phone and not pwd:
                return self.send_fail(error_text="密码登录缺手机号或密码")
            success, user = get_user_by_phone_and_password(phone, pwd, login_type)
            if not success:
                return self.send_fail(error_text=user)
            token, refresh_token = self._set_current_user(user)
            response_data = jwt_response_payload_handler(token, refresh_token, user, request)
            return self.send_success(data=response_data)
        # 若登陆方式为手机号
        else:
            if not phone and not sms_code:
                return self.send_fail(error_text="密码登录缺手机号或验证码")
            redis_conn = get_redis_connection("verify_codes")
            real_sms_code = redis_conn.get("sms_%s"%phone)
            if not real_sms_code:
                return self.send_fail(error_text="验证码已过期")
            if str(real_sms_code.decode()) != sms_code:
                return self.send_error(
                    status_code=status.HTTP_400_BAD_REQUEST, error_message={"detail":"短信验证码错误"}
                )
            success, user = get_user_by_phone(phone, login_type)
            if not success:
                return self.send_fail(error_text=user)
            # user不存在，进行注册
            if not user:
                data = {
                    "phone": phone,
                    "username": phone,
                    "nickname": "用户{phone}".format(phone=phone),
                    "head_image_url": "http://img.senguo.cc/FlMKOOnlycuoZp1rR39LyCFUHUgl"
                }
                serializer = UserCreateSerializer(data=data)
                serializer.is_valid()
                user = serializer.save()
            token, refresh_token = self._set_current_user(user)
            response_data = jwt_response_payload_handler(token, refresh_token, user, request)
            return self.send_success(data=response_data)




class AdminUserLogoutView(SuperBaseView):
    """后台-退出登录"""

    def post(self, request):
        # 前端清除jwt
        user = self._get_current_user(request)
        if not user:
            return self.send_error(
                status_code=status.HTTP_401_UNAUTHORIZED, error_message={"detail": "用户未登录"}
            )
        return self.send_success()


class MallUserView(MallBaseView):
    """商城-用户-登录"""
    # 父类进行了登录验证，这里覆盖掉
    authentication_classes = ()

    @use_args(
        {
            "code": fields.String(required=False, comment="微信code"),
            "phone": fields.String(required=False, validate=[validate.Regexp(PHONE_RE)], comment="手机号"),
            "sms_code": fields.String(required=False, comment="短信验证码"),
            "password": DecryptPassword(required=False, validate=[validate.Regexp(PASSWORD_RE)], comment="密码"),
            "login_type": fields.Integer(
                required=True,
                validate=[validate.OneOf(
                    [UserLoginType.WX, UserLoginType.PWD, UserLoginType.PHONE]
                )],
                comment="登录方式,0:微信，1：密码，2：手机"
            )
        }, location="json",
    )
    def post(self, request, args, shop_code):
        login_type = args["login_type"]
        code = args.get("code", None)
        phone = args.get("phone", None)
        pwd = args.get("password", None)
        sms_code = args.get("sms_code", None)
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        # todo 微信登录还需要修改
        # 若登录方式为微信
        if login_type == UserLoginType.WX:
            if not code:
                return self.send_fail(error_text="微信登录缺少code")
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
                    "username":user_info.get('phone'),
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
                user = user_serializer.save()
            ret, user_openid = get_openid_by_user_id_and_appid(user.id, shop_appid)
            # 不存在则添加用户的openid
            if not ret:
                info = {
                    'user_id': user.id,
                    'mp_appid': shop_appid,
                    'wx_openid': user_info.get("openid"),
                }
                create_user_openid(**info)
        # 若登录方式为密码
        elif login_type == UserLoginType.PWD:
            if not phone and not pwd:
                return self.send_fail(error_text="密码登录缺手机号或密码")
            success, user = get_user_by_phone_and_password(phone, pwd, login_type)
            if not success:
                return self.send_fail(error_text=user)
        # 若登陆方式为手机号
        else:
            if not phone and not sms_code:
                return self.send_fail(error_text="密码登录缺手机号或验证码")
            redis_conn = get_redis_connection("verify_codes")
            real_sms_code = redis_conn.get("sms_%s" % phone)
            if not real_sms_code:
                return self.send_fail(error_text="验证码已过期")
            if str(real_sms_code.decode()) != sms_code:
                return self.send_error(
                    status_code=status.HTTP_400_BAD_REQUEST, error_message={"detail": "短信验证码错误"}
                )
            success, user = get_user_by_phone(phone, login_type)
            if not success:
                return self.send_fail(error_text=user)
            # user不存在
            if not user:
                return self.send_fail(error_text="该用户不存在")
        customer = get_customer_by_user_id_and_shop_id_interface(user.id, shop.id)
        # 新客户则创建客户信息
        if not customer:
            create_customer(user.id, shop.id)
        token, refresh_token = self._set_current_user(user)
        response_data = jwt_response_payload_handler(token, refresh_token, user, request)
        return self.send_success(data=response_data)


class MallUserRegisterView(MallBaseView):
    """商城-用户-注册"""
    # 父类进行了登录验证，这里覆盖掉
    authentication_classes = ()

    @use_args(
        {
            "phone": fields.String(required=True, validate=[validate.Regexp(PHONE_RE)], comment="手机号"),
            "sms_code": fields.String(required=True, comment="短信验证码"),
            "password1": fields.String(required=True, comment="密码1"),
            "password2": fields.String(required=True, comment="密码2"),
        }, location="json",
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        phone = args.get("phone")
        sms_code = args.get("sms_code")
        # 验证密码是否一致
        if args.get("password1") != args.get("password2"):
            return self.send_fail(error_text="两次输入的密码不一致")
        # 校验验证码
        redis_conn = get_redis_connection("verify_codes")
        real_sms_code = redis_conn.get("sms_%s" % phone)
        if not real_sms_code:
            return self.send_fail(error_text="验证码已过期")
        if str(real_sms_code.decode()) != sms_code:
            return self.send_error(
                status_code=status.HTTP_400_BAD_REQUEST, error_message={"detail": "短信验证码错误"}
            )
        data = {
            "phone": phone,
            "username": phone,
            "nickname": "用户{phone}".format(phone=phone),
            "head_image_url": "http://img.senguo.cc/FlMKOOnlycuoZp1rR39LyCFUHUgl",
            "password": args.get("password1")
        }
        serializer = UserCreateSerializer(data=data)
        serializer.is_valid()
        user = serializer.save()
        customer = get_customer_by_user_id_and_shop_id_interface(user.id, shop.id)
        # 新客户则创建客户信息
        if not customer:
            create_customer(user.id, shop.id)
        token, refresh_token = self._set_current_user(user)
        response_data = jwt_response_payload_handler(token, refresh_token, user, request)
        return self.send_success(data=response_data)


class MallUserAuthorizationView(MallBaseView):
    """商城-用户-用户登录认证"""

    def post(self, request, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        user = self.current_user
        serializer = UserSerializer(user)
        # 额外查询用户的积分数据
        customer = get_customer_by_user_id_and_shop_id_interface(user.id, shop.id)
        customer_info = dict(serializer.data)
        customer_info["points"] = round(float(customer.point), 2) if customer else 0
        customer_info["is_new_customer"] = (
            customer.is_new_customer() if customer else True
        )
        return self.send_success(data=customer_info)


class SMSCodeView(GlobalBaseView):
    """用户-发送短信验证码接口"""

    @use_args(
        {
            "phone": fields.String(
                required=True, validate=[validate.Regexp(PHONE_RE)], comment="手机号"
            )
        },
        location="json"
    )
    def post(self, request, args):
        phone = args["phone"]
        if self.request.META.get('HTTP_X_FORWARDED_FOR'):
            remote_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            remote_ip = self.request.META.get("REMOTE_ADDR")
        phone_ip = "bind_phone_ip:%s:%s" % (phone, remote_ip)
        redis_conn = get_redis_connection("verify_codes")
        if redis_conn.get(phone_ip):
            return self.send_fail(error_text="一分钟只能发生一次")
        sms_code = gen_sms_code()
        print("sms_code: ", sms_code)  # 测试用

        # 在发送短信验证码前保存数据，以免多次访问和注册时验证
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % (phone), 300, sms_code) # 验证码过期时间300秒
        pl.setex(phone_ip, 60, 1) # 验证码60秒发送一次
        pl.execute()
        # try:
        #     # # 调用第三方接口发送短信
        #     use = "绑定手机号"
        #     # 先用腾讯发,失败就云片用发
        #     ret, info = TencentSms.send_tencent_verify_code(phone, sms_code, use)
        #     if not ret:
        #         ret, info = YunPianSms.send_yunpian_verify_code(phone, sms_code, use)
        #     if not ret:
        #         return self.send_fail(error_text=info)
        # except Exception as e:
        #     print(e)
        #     return self.send_fail(error_text="短信发送失败")
        return self.send_success()
