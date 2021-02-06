class ShopPayChannelType:
    LCSW = 1
    CCB = 2


class ShopStatus:
    REJECTED = 3  # 已拒绝
    CHECKING = 2  # 审核中
    NORMAL = 1  # 已通过,正常
    CLOSED = 0  # 店铺已关闭


# 店铺是否开通认证
class ShopVerifyActive:
    NO = 0  # 未认证
    YES = 1  # 已认证
    CHECKING = 2  # 审核中
    REJECTED = 3  # 已拒绝


# 店铺类型,个人or企业
class ShopVerifyType:
    ENTERPRISE = 0  # 企业
    INDIVIDUAL = 1  # 个人


# 店铺是否开通支付
class ShopPayActive:
    REJECTED = 3  # 已拒绝
    CHECKING = 2  # 审核中
    YES = 1  # 已开通
    NO = 0  # 未开通


# 店铺公众号是否开启
class ShopMpMpActive:
    YES = 1
    NO = 0


# 店铺公众号服务类型
class ShopMpServiceType:
    SUBSCRIBE = 1
    OLD_SUBSCRIBE = 2
    SERVICE = 3


# 店铺授权森果是否开启
class ShopMpAuthorizeActive:
    AUTH_NOT_BIND = 2  # 未绑定,但是微信后台为解绑,实际还可以用,只是在森果显示未绑定(已授权)
    AUTH = 1  # 已绑定(已授权)
    NOT_AUTH = 0  # 真的未绑定(未授权)


# 店铺微信认证类型
class ShopMpVerifyType:
    NOT_BIND = -1  # 未绑定
    NOT_VERIFY = 0  # 未验证
    MP_VERIFY = 1  # 微信认证
    SINA_VERIFY = 2  # 新浪微博认证
    T_QQ_VERIFY = 3  # 腾讯微博认证
    VERIFY_BUT_NOT_NAME = 4  # 已认证但未通过名称认证
    VERIFY_BUT_NOT_NAME_BUT_SINA = 5  # 已认证但未通过名称认证,但通过了新浪微博认证
    VERIFY_BUT_NOT_NAME_BUT_T_QQ = 6  # 已认证但未通过名称认证,但通过了腾讯微博认证