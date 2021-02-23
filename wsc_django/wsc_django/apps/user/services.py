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


def create_user_openid(user_openid_info: dict):
    """
    创建用户openID
    :param user_openid_info:
    :return:
    """
    user_openid = UserOpenid.objects.create(**user_openid_info)
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


def get_openid_by_user_and_appid(user_id: int, mp_appid: str):
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