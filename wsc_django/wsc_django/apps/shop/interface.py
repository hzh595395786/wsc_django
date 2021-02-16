from staff.services import list_staff_by_user_id


def list_staff_by_user_id_interface(user_id: int, roles: int) -> list:
    """获取一个用户的所有员工信息"""
    staff_list = list_staff_by_user_id(user_id, roles)
    return staff_list