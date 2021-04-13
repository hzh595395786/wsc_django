from logs.services import create_config_log
from shop.models import Shop
from shop.services import update_shop_data
from staff.services import get_staff_by_user_id_and_shop_id_with_user


def create_config_log_interface(log_info: dict):
    """创建设置日志"""
    log = create_config_log(log_info)
    return log


def update_shop_data_interface(shop: Shop, args: dict):
    """修改店铺信息"""
    shop = update_shop_data(shop, args)
    return shop


def get_staff_by_user_id_and_shop_id_with_user_interface(
    user_id: int, shop_id: int
):
    """通过shop_id与user_id获取员工"""
    staff = get_staff_by_user_id_and_shop_id_with_user(user_id, shop_id)
    return staff