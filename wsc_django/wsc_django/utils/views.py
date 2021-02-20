"""自己定义的视图类"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.services import get_shop_by_shop_id, get_shop_by_shop_code
from staff.constant import StaffRole, StaffPermission
from staff.services import get_staff_by_user_id_and_shop_id
from user.models import User


class GlobalBaseView(APIView):
    """
    通用的请求处理基类，主要定义了一些API通信规范和常用的工具
    响应处理：
        一个请求在逻辑上分为三个结果：请求错误、请求失败和请求成功。请求错误会通常
        是由于请求不合法（如参数错误、请求不存在、token无效等），直接返回http状
        态码；请求失败通常是由于一些事物逻辑上的错误，比如库存不够、余额不足等；请
        求成功不解释

        请求失败: send_error(status_code, **kargs)[返回JSON数据格式: {"success":False, "code":fail_code, "text":fail_text}]
        请求成功: send_fail(fail_code, fail_text)[返回JSON数据格式:{"success":True, **kwargs}]
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

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, Response):
            pass
        else:
            response = Response(data=response)
        return super().finalize_response(request, response, *args, **kwargs)


class UserBaseView(GlobalBaseView):
    """用户的基类，用来处理认证"""

    def initialize_request(self, request, *args, **kwargs):
        # todo 设置当前用户
        # 仅测试使用下代码
        user = User.objects.get(id=1)
        request.user = user
        return super().initialize_request(request, *args, **kwargs)


class StaffBaseView(UserBaseView):
    """员工的基类，用来处理是否有效员工"""
    staff_roles = StaffRole
    staff_permissions = StaffPermission

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        wsc_shop_id = request.COOKIES.get("wsc_shop_id", 0)
        # 从cookie中获取shop_id进行查询
        shop = get_shop_by_shop_id(int(wsc_shop_id))
        request.shop = shop
        # todo user的取得后续还需修改
        current_staff = get_staff_by_user_id_and_shop_id(request.user.id, request.shop.id)
        self.current_staff = current_staff
        return request


class AdminBaseView(StaffBaseView):
    """管理员的基类"""
    pass


class MallBaseView(UserBaseView):
    """商城基类"""

    def _set_current_shop(self, request, shop_code):
        """设置当前商铺"""
        shop = get_shop_by_shop_code(shop_code)
        request.shop = shop

