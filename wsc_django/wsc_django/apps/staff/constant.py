class StaffStatus:
    """员工状态"""

    NORMAL = 1
    DELETED = 0


class StaffRole:
    """员工角色"""

    SHOP_SUPER_ADMIN = 0xFF  # 店铺超管, 预留两位
    SHOP_ADMIN = 0x08  # 店铺管理员


class StaffPermission:
    """员工权限"""

    ADMIN_DASHBORD = 0x01
    ADMIN_ORDER = 0x02
    ADMIN_PRODUCT = 0x04
    ADMIN_CUSTOMER = 0x08
    ADMIN_PROMOTION = 0x10
    ADMIN_STAFF = 0x20
    ADMIN_CONFIG = 0x40


class StaffApplyStatus:
    """员工申请状态"""

    UNAPPlY = -1 # 未申请
    APPLYING = 1 # 申请中
    PASS = 2 # 已通过


class StaffApplyExpired:
    """员工申请是否过期,当员工被删除之后,将之前的所有申请全部过期,就可以再次申请,否则不能再次申请"""

    YES = 1 # 已过期
    NO = 0 # 未过期
