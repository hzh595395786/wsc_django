class CustomerPointType:
    FIRST = 1
    CONSUME = 2
    REFUND = 3


# TODO 待补充
CUSTOMER_POINT_TYPE = {
    CustomerPointType.FIRST: "店铺首单",
    CustomerPointType.CONSUME: "购买货品",
    CustomerPointType.REFUND: "退款",
}


class MineAddressDefault:
    YES = 1
    NO = 0


class MineAddressStatus:
    NORMAL = 1
    DELETE = 0