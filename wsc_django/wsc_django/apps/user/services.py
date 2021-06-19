import re

from django_redis import get_redis_connection

from settings import QINIU_SHOP_IMG_HOST
from shop.constant import ShopPayChannelType
from shop.models import PayChannel
from user.constant import UserLoginType
from user.models import User, UserOpenid


def create_user(user_info: dict):
    """
    创建一个user
    :param user_info:
    :return:
    """
    user = User(**user_info)
    if user_info.get("password", None):
        user.set_password(user_info.get("password"))
    if not re.match(r'^http(s)?://.+$', user.head_image_url):
        user.head_image_url = QINIU_SHOP_IMG_HOST + user.head_image_url
    user.save()
    return user


def create_user_openid(user_id: int, mp_appid: str, wx_openid: str):
    """
    创建用户openID
    :param user_openid_info:
    :return:
    """
    user_openid = UserOpenid(user_id=user_id, mp_appid=mp_appid, wx_openid=wx_openid)
    user_openid.save()
    return user_openid


def update_user_basic_data(user: User, user_data: dict):
    """
    修改用户基本信息
    :param user:
    :param user_data:{
                nickname:nickname,
                realname:realname,
                sex:sex,
                phone:phone,
           }
    :return:
    """
    for k,v in user_data.items():
        setattr(user, k, v)
    user.save()
    return user


def update_user_phone(user: User, phone: str):
    """
    修改用户绑定的手机号
    :param user:
    :param phone:
    :return:
    """
    res, search_user = get_user_by_phone(phone, UserLoginType.PHONE)
    if search_user:
        return False, "该手机号已绑定其他用户"
    user.phone = phone
    user.save()
    return True, user


def update_user_password(user: User, password1: str, password2: str):
    """
    修改用户的密码
    :param password1:
    :param password2:
    :return:
    """
    if password1 != password2:
        return False, "两次输入的密码不一致"
    user.set_password(password1)
    user.save()
    return True, ""


def validate_sms_code(phone: str, sms_code: str):
    """
    验证短信验证码
    :param phone:
    :param sms_code:
    :return:
    """
    redis_conn = get_redis_connection("verify_codes")
    real_sms_code = redis_conn.get("sms_%s" % phone)
    if not real_sms_code:
        return False, "验证码已过期"
    if str(real_sms_code.decode()) != sms_code:
        return False, "短信验证码错误"
    return True, ""


def send_email(user: User, email: str):
    """
    发送验证邮件
    :param user:
    :param email:
    :return:
    """
    if user.email != email:
        return False, "激活邮箱与绑定邮箱不一致"
    if user.email_active:
        return False, "该邮箱已激活，无需重复操作"
    # 生成激活链接
    url = user.generate_verify_email_url()
    # 发送邮件
    print(url)
    return True, ""


def get_user_by_id(user_id: int):
    """
    通过用户id获取用户
    :param user_id:
    :return:
    """
    user = User.objects.filter(id=user_id).first()
    return user


def get_user_by_phone(phone: str, login_type: int):
    """
    通过手机号获取用户, 登录方式必须为手机号
    :param phone:
    :param login_type:
    :return:
    """
    if login_type !=  UserLoginType.PHONE:
        return False, "登录方式必须为手机号登录"
    user = User.objects.filter(phone=phone).first()
    return True, user


def get_user_by_phone_and_password(phone: str, password: str, login_type: int):
    """
    通过手机号获取用户和密码, 登录方式必须为密码
    :param phone:
    :param password:
    :return:
    """
    if login_type != UserLoginType.PWD:
        return False, "登录方式必须为密码登录"
    user = User.objects.filter(phone=phone).first()
    if not user:
        return False, "用户不存在"
    if not user.password:
        return False, "用户还未设置密码，请用手机号登录"
    if not user.check_password(password):
        return False, "密码不正确"
    return True, user


def get_user_by_wx_unionid(wx_unionid: str):
    """
    通过微信unionid获取一个用户
    :param wx_unionid:
    :return:
    """
    user = User.objects.filter(wx_unionid=wx_unionid).first()
    return user


def get_openid_by_user_id_and_appid(user_id: int, mp_appid: str):
    """
    通过用户id和公众号的mp_appid获取用户的wx_openid
    :param user_id:
    :param mp_appid:
    :return:
    """
    user_openid = UserOpenid.objects.filter(user_id=user_id, mp_appid=mp_appid).first()
    if not user_openid:
        return False, 'openid不存在'
    return True, user_openid


def get_user_by_email(email: str):
    """
    通过用户邮箱获取用户
    :param email:
    :return:
    """
    user = User.objects.filter(email=email).first()
    return user


def get_pay_channel_by_shop_id(shop_id: int):
    """
    通过商铺id获取支付渠道信息
    :param shop_id:
    :return:
    """
    shop_pay_channel = PayChannel.objects.filter(shop_id=shop_id).first()
    if not shop_pay_channel:
        return False, "店铺未开通线上支付"
    elif shop_pay_channel.channel_type != ShopPayChannelType.LCSW:
        return False, "店铺支付渠道错误"
    return True, shop_pay_channel


def list_user_by_ids(user_ids: list):
    """
    通过id列表获取user列表
    :param user_ids:
    :return:
    """
    user_list = User.objects.filter(id__in=user_ids).all()
    return user_list


def list_openid_by_user_ids_and_appid(user_ids: list, mp_appid: str):
    """
    通过user_ids与mp_appid列出wx_openid
    :param user_ids:
    :param mp_appid:
    :return:
    """
    user_openid_list = UserOpenid.objects.filter(user_id__in=user_ids, mp_appid=mp_appid).all()
    return user_openid_list