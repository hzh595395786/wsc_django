from wechatpy import WeChatClient
from wechatpy.client.api import WeChatWxa
from qcloud_cos import CosConfig, CosS3Client, CosServiceError

from settings import (
    MINI_PROGRAM_APPID,
    MINI_PROGRAM_APPSECRET,
    TENCENT_COS_SECRETID,
    TENCENT_COS_SECRETKEY,
    TENCENT_COS_IMG_HOST,
)


def get_shop_mini_program_qcode(shop_code):
    """
    获取店铺的小程序码
    :param shop_code: 商铺编号
    :return:
    """
    appid = MINI_PROGRAM_APPID
    secret = MINI_PROGRAM_APPSECRET
    wechat_client = WeChatClient(appid, secret)
    mini_program = WeChatWxa(wechat_client)
    path = '/pages/index/index?shop_code=%s'%shop_code
    try:
        qcode_file = mini_program.create_qrcode(path).content
    except Exception as e:
        print(e)
        return None
    return qcode_file


def put_qcode_file_to_tencent_cos(qcode_file, shop_code):
    """
    将小程序码文件上传到腾讯云cos并返回url
    :param qcode_file: 小程序码文件流
    :param shop_code: 商铺编号，用来作为文件名
    :return:
    """
    secret_id = TENCENT_COS_SECRETID
    secret_key = TENCENT_COS_SECRETKEY
    region = 'ap-nanjing'  # 区域
    bucket = 'zhihao-1300126182'  # 桶名词
    token = None  # 使用临时密钥需要传入Token，默认为空,可不填
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
    client = CosS3Client(config)
    key = 'img/' + shop_code + '.png'  # 文件名
    try:
        response = client.put_object(
            Bucket=bucket,
            Body=qcode_file,
            Key=key,
            ContentType='image/png'
        )
    except CosServiceError as e:
        return False, e.get_error_msg()
    if not response.get("ETag", None):
        return False, "上传失败"
    return True, TENCENT_COS_IMG_HOST + key