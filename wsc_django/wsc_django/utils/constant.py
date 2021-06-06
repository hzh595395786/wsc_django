class DateFormat:
    YEAR = "%Y"
    MONTH = "%Y-%m"
    DAY = "%Y-%m-%d"
    TIME = "%Y-%m-%d %H:%M:%S"


PHONE_RE = r"^1[0-9]{10}$"


PASSWORD_RE = r"^(?![0-9]+$)(?![a-z]+$)[0-9a-z]{8,16}$"


EMAIL_RE = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"