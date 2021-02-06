# 打印机品牌
class PrinterBrand:
    YILIANYUN = 1
    FEIYIN = 2
    FOSHANXIXUN = 3
    S1 = 4
    S2 = 5
    SENGUO = 6


PRINTER_BRAND_TEXT = {PrinterBrand.YILIANYUN: "易联云"}


# 打印机类型
class PrinterType:
    LOCAL = 1
    NET = 2


# 打印模板
class PrinterTemp:
    ONE = 1


# 订单自动打印
class PrinterAutoPrint:
    YES = 1
    NO = 0


# 打印机状态
class PrinterStatus:
    NORMAL = 1
    DELETE = 0


# 打印订单号条码
class ReceiptBrcodeActive:
    YES = 1
    NO = 0


# 分享设置模板信息
class ShareSetUpTemplate:
    CUSTOM_TITLE_NAME = "精打细算，还是来这划算!【{shop_name}】"  # 自定义标题名称模板
    CUSTOM_SHARE_DESCRIPTION = "我发现了一家很不错的店铺，地址分享给你，快来一起买买买吧！"  # 自动以分享描述模板
