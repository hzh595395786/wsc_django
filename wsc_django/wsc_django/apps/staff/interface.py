from logs.services import create_staff_log


def create_staff_log_interface(log_info: dict):
    """创建一个员工板块的日志"""
    log = create_staff_log(log_info)
    return log