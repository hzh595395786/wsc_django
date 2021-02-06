# 货品库存变记录更类型
class ProductStorageRecordType:
    MANUAL_MODIFY = 1  # 手动修改
    MALL_SALE = 2  # 商城售出
    ORDER_CANCEL = 3  # 订单取消
    ORDER_REFUND = 4  # 订单退款


PRODUCT_STORAGE_RECORD_TYPE = {
    ProductStorageRecordType.MANUAL_MODIFY: "手动修改",
    ProductStorageRecordType.MALL_SALE: "商城售出",
    ProductStorageRecordType.ORDER_CANCEL: "订单取消",
    ProductStorageRecordType.ORDER_REFUND: "订单退款",
}


# 货品库存变更记录状态, 预留用
class ProductStorageRecordStatus:
    NORMAL = 1
    DELETE = 0


# 库存变更记录的操作人
class ProductStorageRecordOperatorType:
    STAFF = 1  # 员工
    CUSTOMER = 2  # 客户


PRODUCT_STORAGE_RECORD_OPERATOR_TYPE = {
    ProductStorageRecordOperatorType.STAFF: "员工",
    ProductStorageRecordOperatorType.CUSTOMER: "客户",
}
