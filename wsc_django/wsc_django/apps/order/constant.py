# 订单状态
class OrderStatus:
    CANCELED = 0  # 已取消
    UNPAID = 1  # 待支付
    PAID = 2  # 已支付，未处理
    CONFIRMED = 3  # 已确认，处理中  -- 待自提,平配送中
    FINISHED = 4  # 已完成
    REFUNDED = 5  # 已退款
    REFUND_FAIL = 6  # 退款失败
    WAITTING = 11  # 等待成团


# 订单支付方式
class OrderPayType:
    WEIXIN_JSAPI = 1  # 微信支付
    ON_DELIVERY = 2  # 货到付款


# 订单配送方式
class OrderDeliveryMethod:
    HOME_DELIVERY = 1  # 送货上门
    CUSTOMER_PICK = 2  # 客户自提


# 订单类型
class OrderType:
    NORMAL = 1  # 普通订单
    GROUPON = 5  # 拼团订单


# 订单退款类型
class OrderRefundType:
    WEIXIN_JSAPI_REFUND = 1  # 微信退款
    UNDERLINE_REFUND = 2  # 线下退款


MAP_EVENT_ORDER_TYPE = {
    0: OrderType.NORMAL,  # 没活动,普通订单
    1: OrderType.GROUPON,  # 拼团活动, 拼团订单
}
