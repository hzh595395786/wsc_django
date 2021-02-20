from user.models import User


def get_user_by_id(user_id: int):
    """
    通过用户id获取用户
    :param user_id:
    :return:
    """
    user = User.objects.filter(id=user_id).first()
    return user