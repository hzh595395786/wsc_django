class GrouponType:
    NORMAL = 1  # 普通拼团
    MENTOR = 2  # 老带新


class GrouponStatus:
    ON = 1  # 启用
    OFF = 2  # 停用
    EXPIRED = 3  # 过期


class GrouponAttendStatus:
    EXPIRED = -1  # 已过期
    CREATED = 0  # 已创建
    WAITTING = 1  # 拼团中
    SUCCEEDED = 2  # 已成团
    FAILED = 3  # 已失败


class GrouponAttendLineStatus:
    EXPIRED = -1  # 已过期
    UNPAID = 0  # 未付款
    PAID = 1  # 已付款
