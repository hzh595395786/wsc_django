class OperateLogModule:
    """操作记录统一表模块"""

    # DASHBORD = 1
    ORDER = 2
    PRODUCT = 3
    # CUSTOMER = 4
    PROMOTION = 5
    STAFF = 6
    CONFIG = 7


class OrderLogType:
    """订单日志类型"""

    PRINT = 1  # 打印订单
    DIRECT = 2  # 一键完成
    CONFIRM = 3  # 开始处理,确认订单
    FINISH = 4  # 完成订单
    REFUND = 5  # 退款
    HOME_MINIMUM_ORDER_AMOUNT = 6  # 配送模式起送金额
    HOME_DELIVERY_AMOUNT = 7  # 配送模式配送费
    HOME_MINIMUM_FREE_AMOUNT = 8  # 配送模式免配送费最小金额
    PICK_SERVICE_AMOUNT = 9  # 自提模式服务费
    PICK_MINIMUM_FREE_AMOUNT = 10  # 自提模式免服务费最小金额
    REFUND_FAIL = 11  # 退款失败
    _SYS_PRINT = 99  # 不对外开放,不用于日志记录
    _SYS_REFUND = 98  # 不对外开放,不用于日志记录


MAP_NO_OPERATOR_ORDER_TYPE = {
    OrderLogType.PRINT: OrderLogType._SYS_PRINT,
    OrderLogType.REFUND: OrderLogType._SYS_REFUND,
    OrderLogType.REFUND_FAIL: OrderLogType.REFUND_FAIL,
}


ORDER_LOG_TYPE = {
    OrderLogType.PRINT: "打印订单",
    OrderLogType.DIRECT: "一键完成",
    OrderLogType.CONFIRM: "开始处理",
    OrderLogType.FINISH: "完成订单",
    OrderLogType.REFUND: "订单退款",
    OrderLogType.HOME_MINIMUM_ORDER_AMOUNT: "起送金额",
    OrderLogType.HOME_DELIVERY_AMOUNT: "配送费",
    OrderLogType.HOME_MINIMUM_FREE_AMOUNT: "免配送费金额",
    OrderLogType.PICK_SERVICE_AMOUNT: "服务费",
    OrderLogType.PICK_MINIMUM_FREE_AMOUNT: "免服务费金额",
    OrderLogType._SYS_PRINT: "系统自动打印订单",
    OrderLogType._SYS_REFUND: "拼团失败，系统自动退款",
    OrderLogType.REFUND_FAIL: "退款失败，系统自动退款失败",
}


class StaffLogType:
    """员工日志类型"""

    ADD_STAFF = 1
    DELETE_STAFF = 2


STAFF_LOG_TYPE = {StaffLogType.ADD_STAFF: "添加员工", StaffLogType.DELETE_STAFF: "删除员工"}


class ProductLogType:
    """货品操作日志类型"""

    ADD_PRODUCT = 1
    DELETE_PRODUCT = 2
    ADD_PRODUCT_GROUP = 3
    DELETE_PRODUCT_GROUP = 4
    UPDATE_PRODUCT_GROUP = 5
    ON_PRODUCT = 6
    OFF_PRODUCT = 7


PRODUCT_LOG_TYPE = {
    ProductLogType.ADD_PRODUCT: "添加货品",
    ProductLogType.DELETE_PRODUCT: "删除货品",
    ProductLogType.ADD_PRODUCT_GROUP: "添加货品分组",
    ProductLogType.DELETE_PRODUCT_GROUP: "删除货品分组",
    ProductLogType.UPDATE_PRODUCT_GROUP: "修改货品分组",
    ProductLogType.ON_PRODUCT: "上架货品",
    ProductLogType.OFF_PRODUCT: "下架货品",
}


class ConfigLogType:
    """设置模块日志类型"""

    SHOP_NAME = 1
    SHOP_PHONE = 2
    PRINTER_SET = 3


CONFIG_LOG_TYPE = {
    ConfigLogType.SHOP_NAME: "店铺名称",
    ConfigLogType.SHOP_PHONE: "联系电话",
    ConfigLogType.PRINTER_SET: "打印机设置",
}


class PromotionLogType:
    """玩法模块日志类型"""

    ADD_GROUPON = 1
    STOP_GROUPON = 2
    UPDATE_GROUPON = 3


PROMOTION_LOG_TYPE = {
    PromotionLogType.ADD_GROUPON: "新建拼团",
    PromotionLogType.STOP_GROUPON: "停用拼团",
    PromotionLogType.UPDATE_GROUPON: "编辑拼团",
}
