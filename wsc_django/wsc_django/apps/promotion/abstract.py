class AbstractPromotionRule:
    """ 抽象促销活动规则类，定义促销活动的接口，由子类实现接口 """

    def limit(self, *args, **kwargs):
        """ 促销的限制性规则，用于优惠的下限，比如订单最小达到多少钱可以配送，用户限制使用多少优惠券等 """
        raise NotImplementedError

    def calculate(self, *args, **kwargs):
        """ 促销的计算型规则，返回当前优惠提供的优惠金额 """
        raise NotImplementedError

class PromotionEventTemplate:
    """ 促销活动事件模板类，用于事件发布 """

    _event_type = None

    def __init__(self, content: dict):
        self.content = content

    def get_event(self) -> dict:
        if not self._event_type:
            raise NotImplementedError("必须由子类覆盖事件类型")
        self.content.update({"event_type": self._event_type})
        return self.content

    def __getattr__(self, name):
        if self.content.get(name) is not None:
            return self.content[name]
        raise AttributeError(
            "{.__name__!r} object has no attribute {!r}".format(type(self), name)
        )