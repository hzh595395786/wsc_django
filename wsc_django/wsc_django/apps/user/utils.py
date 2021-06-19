import jwt
import warnings
import uuid

from calendar import timegm
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.compat import get_username
from rest_framework_jwt.compat import get_username_field
from rest_framework_jwt.settings import api_settings


jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


def jwt_response_payload_handler(token, refresh_token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'refresh_token': refresh_token,
        'user_id': user.id,
        'nickname': user.nickname,
    }


def jwt_payload_handler(user, expiration_delta, token_type='access_token'):
    """
    根据DRF-JWT的payload进行了一点自行化的修改
    如：1.增加了自定义有效期
       2.在荷载中加入了密文密码，保证了密码修改后token失效
       3.在荷载中加入了token类型，分别为access_token和refresh_token
    """
    username_field = get_username_field()
    username = get_username(user)

    warnings.warn(
        'The following fields will be removed in the future: '
        '`email` and `user_id`. ',
        DeprecationWarning
    )

    payload = {
        'user_id': user.pk,
        'username': username,
        'password': user.password,
        'token_type': token_type,
        'exp': datetime.utcnow() + expiration_delta
    }
    if hasattr(user, 'email'):
        payload['email'] = user.email
    if isinstance(user.pk, uuid.UUID):
        payload['user_id'] = str(user.pk)

    payload[username_field] = username

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


class ZhiHaoJWTAuthentication(JSONWebTokenAuthentication):
    """志浩web项目自定义jwt验证类（根据DRF-JWT改写）"""

    def authenticate_token(self, token):
        """用于校验token值，基于authenticate方法改写"""
        try:
            payload = jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            print('Signature has expired.')
            return False
        except jwt.DecodeError:
            print('Error decoding signature.')
            return False
        except jwt.InvalidTokenError:
            return False
        try:
            user = self.authenticate_credentials(payload)
        except Exception as e:
            print(e)
            return False
        return user

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        注：根据自定义载荷改写的自定义验证，基于BaseJSONWebTokenAuthentication父类的同名方法改写
        """
        User = get_user_model()
        username = jwt_get_username_from_payload(payload)
        password = payload.get('password')

        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        if user.password != password:
            msg = _('User have update password')
            raise exceptions.AuthenticationFailed(msg)

        return user