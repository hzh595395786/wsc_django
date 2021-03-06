from shop.constant import ShopPayChannelType
from shop.models import PayChannel
from user.models import User, UserOpenid


def create_user(user_info: dict):
    """
    创建一个user
    :param user_info:
    :return:
    """
    user = User.objects.create(**user_info)
    user.save()
    return user


def create_user_openid(user_id: int, mp_appid: str, wx_openid: str):
    """
    创建用户openID
    :param user_openid_info:
    :return:
    """
    user_openid = UserOpenid.objects.create(user_id=user_id, mp_appid=mp_appid, wx_openid=wx_openid)
    user_openid.save()
    return user_openid


def get_user_by_id(user_id: int):
    """
    通过用户id获取用户
    :param user_id:
    :return:
    """
    user = User.objects.filter(id=user_id).first()
    return user


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


def list_user_by_ids(user_ids: list):
    """
    通过id列表获取user列表
    :param user_ids:
    :return:
    """
    user_list = User.objects.filter(id__in=user_ids).all()
    return user_list


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


def list_openid_by_user_ids_and_appid(user_ids: list, mp_appid: str):
    """
    通过user_ids与mp_appid列出wx_openid
    :param user_ids:
    :param mp_appid:
    :return:
    """
    user_openid_list = UserOpenid.objects.filter(user_id__in=user_ids, mp_appid=mp_appid).all()
    return user_openid_list