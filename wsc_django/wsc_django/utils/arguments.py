import json

from webargs.fields import Field
from webargs import ValidationError

class StrToList(Field):
    """字符串转列表list(int)"""

    def __init__(self, split_str: str = ",", if_int: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.split_str = split_str
        self.trans_type = int if if_int else str

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, (str, bytes)):
            raise self.make_error("invalid")
        try:
            res_list = []
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            value = value.replace(" ", "")
            value_list = value.split(self.split_str) if value else []
            for v in value_list:
                res_list.append(self.trans_type(v))
            return res_list
        except Exception as e:
            raise ValidationError(str(e))


class StrToDict(Field):
    """字符串转dict"""

    def _deserialize( self, value, attr, data, **kwargs ):
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            try:
                return json.loads(value)
            except Exception as e:
                raise ValidationError("value error must json str")
        else:
            raise ValidationError("value type error")