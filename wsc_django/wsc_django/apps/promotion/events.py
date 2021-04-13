""" 具体的优惠活动事件 """
from promotion.abstract import PromotionEventTemplate


class GrouponEvent(PromotionEventTemplate):
    _event_type = "1"