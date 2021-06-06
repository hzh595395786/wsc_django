USER_OUTPUT_CONSTANT = (
    "head_image_url",
    "nickname",
    "realname",
    "sex",
    "phone",
    "birthday",
    # "passport_id",
)


class Sex:
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class UserLoginType:
    WX = 0
    PWD = 1
    PHONE = 2


VERIFY_EMAIL_TOKEN_EXPIRES = 24 * 60 * 60
