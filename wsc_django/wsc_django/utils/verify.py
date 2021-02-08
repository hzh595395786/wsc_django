"""加密验证相关"""
import binascii
from Crypto.Cipher import DES
from rest_framework.authentication import BaseAuthentication


class WSCPermission(BaseAuthentication):
    """微商城权限验证"""

    def has_permission(self, request, views):
        sign = request.get("sign")
        key = SimpleEncrypt.decrypt(sign)
        key_list = key.split("@")
        params = ("passport_id", "timestamp")
        if len(key_list) != len(params):
            return False
        for index, v in enumerate(params):
            if key_list[index] != str(request.get(v)):
                return False


class EncryptBase:
    """
        调用示例
        加密:SimpleEncrypt.encrypt('10930')
            返回:'41c836605df56a81'
        解密:SimpleEncrypt.decrypt('41c836605df56a81')
            返回:'10930'
    """

    @classmethod
    def pad(cls, text):
        """
            length需和key长度相等
        """
        while len(text) % cls.crypt_len != 0:
            text += " "
        return text

    @classmethod
    def encrypt(cls, text):
        """
            参数: text-待加密字符串
                  key-DES需要的秘钥
        """
        if not isinstance(text, str):
            text = str(text)
        des = DES.new(cls.crypt_key, DES.MODE_ECB)
        padded_text = cls.pad(text)
        encrypted_text = des.encrypt(padded_text)
        return binascii.hexlify(encrypted_text).decode()

    @classmethod
    def decrypt(cls, text):
        if not isinstance(text, str):
            text = str(text)
        try:
            encrypted_text = binascii.unhexlify(text)
        except:
            return "0"
        des = DES.new(cls.crypt_key, DES.MODE_ECB)
        return des.decrypt(encrypted_text).decode().strip()

    @classmethod
    def decrypt_to_int(cls, text):
        try:
            text = int(cls.decrypt(text))
        except:
            text = 0
        return text

    @classmethod
    def decrypt_to_list(cls, text):
        try:
            text = cls.decrypt(text)
            text_list = text.split(",")
            res_list = []
            for data in text_list:
                try:
                    data = int(data)
                except:
                    continue
                res_list.append(data)
        except:
            res_list = []
        return res_list


class SimpleEncrypt(EncryptBase):
    """
    用于微商城系统数据加密
    """

    crypt_key = "MRhGeb5T"
    crypt_len = 8