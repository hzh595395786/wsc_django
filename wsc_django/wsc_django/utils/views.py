"""自己定义的视图类"""
from rest_framework import status, exceptions
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings

from shop.services import get_shop_by_shop_id, get_shop_by_shop_code
from staff.constant import StaffRole, StaffPermission
from staff.services import get_staff_by_user_id_and_shop_id
from user.models import User
from wsc_django.utils.authenticate import WSCIsLoginAuthenticate
from wsc_django.utils.permission import StaffRolePermission, WSCStaffPermission


class GlobalBaseView(GenericAPIView):
    """
    通用的请求处理基类，主要定义了一些API通信规范和常用的工具
    响应处理：
        一个请求在逻辑上分为三个结果：请求错误、请求失败和请求成功。请求错误会通常
        是由于请求不合法（如参数错误、请求不存在、token无效等），直接返回http状
        态码；请求失败通常是由于一些事物逻辑上的错误，比如库存不够、余额不足等；请
        求成功不解释

        错误请求: send_error(status_code, error_message)
        请求失败: send_fail(fail_code, fail_text)[返回JSON数据格式: {"success":False, "code":fail_code, "text":fail_text}]
        请求成功: send_success(**kwargs)[返回JSON数据格式:{"success":True, **kwargs}]
    """

    def send_success(self, **kwargs):
        obj = {"success": True}
        for k in kwargs:
            obj[k] = kwargs[k]
        return obj

    def send_fail(
            self,
            error_text=None,
            error_code=None,
            error_redirect=None,
            error_key=None,
            error_obj=None,
    ):
        if error_obj:
            error_code = error_obj.error_code
            error_text = error_obj.error_text

        if type(error_code) == int:
            res = {
                "success": False,
                "error_code": error_code,
                "error_text": error_text,
                "error_redirect": error_redirect,
                "error_key": error_key,
            }
        else:
            res = {"success": False, "error_text": error_text}
        return res

    def send_error(self, status_code, error_message: dict=None):
        """后期可以在改进"""
        if error_message:
            return Response(data=error_message, status=status_code)
        else:
            return Response(status=status_code)

    def _get_paginated_data(self, query_set, serializer):
        """进行分页操作"""
        page = self.paginate_queryset(query_set)
        if page is not None:
            serializer = serializer(page, many=True)
            return self.get_paginated_response(serializer.data).data
        else:
            serializer = serializer(query_set, many=True)
            return serializer.data

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, Response):
            pass
        else:
            response = Response(data=response)
        return super().finalize_response(request, response, *args, **kwargs)


class UserBaseView(GlobalBaseView):
    """用户的基类，用来处理认证"""
    authentication_classes = (WSCIsLoginAuthenticate, )

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        # todo 临时使用 免去登录
        # user = self._get_current_user(request)
        user = User.objects.get(id=1)
        self.current_user = user
        # 用于WSCIsLoginAuthenticate中进行验证
        request.current_user = self.current_user
        return request

    def _get_current_user(self, request):
        jwt = JSONWebTokenAuthentication()
        try:
            res = jwt.authenticate(request)
        except Exception as e:
            print(e)
            res = None
        if res:
            user = res[0]
        else:
            user = None
        return user

    def _set_current_user(self, user: User):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token


class StaffBaseView(UserBaseView):
    """员工的基类，用来处理是否有效员工"""

    permission_classes = (WSCStaffPermission,)
    staff_roles = StaffRole
    staff_permissions = StaffPermission

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        wsc_shop_id = request.get_signed_cookie("wsc_shop_id", salt="微商城商铺id")
        # 从cookie中获取shop_id进行查询
        shop = get_shop_by_shop_id(int(wsc_shop_id))
        # # todo 临时使用 免去cookie
        # shop = get_shop_by_shop_id(1)
        self.current_shop = shop
        current_staff = None
        if shop and self.current_user:
            current_staff = get_staff_by_user_id_and_shop_id(self.current_user.id, self.current_shop.id)
        self.current_staff = current_staff
        return request

    @classmethod
    def permission_required(cls, permission_list: list):
        """验证员工权限的装饰器"""
        def inner(func):
            def wrapper(self, *args, **kwargs):
                for permission in permission_list:
                    if self.current_staff.permissions & permission == 0:
                        return Response(status=status.HTTP_403_FORBIDDEN)
                return func(self, *args, **kwargs)

            return wrapper

        return inner


class AdminBaseView(StaffBaseView):
    """管理员的基类"""

    permission_classes = (WSCStaffPermission, StaffRolePermission,)


class MallBaseView(UserBaseView):
    """商城基类"""

    def _set_current_shop(self, request, shop_code):
        """设置当前商铺"""
        shop = get_shop_by_shop_code(shop_code)
        if not shop:
            raise exceptions.NotFound("店铺不存在")
        self.current_shop = shop


