from django.db import models

# Create your models here.
from shop.models import Shop
from user.models import User
from wsc_django.utils.models import TimeBaseMixin
from staff.constant import (
    StaffStatus,
    StaffApplyStatus,
    StaffApplyExpired,
)


class Staff(models.Model, TimeBaseMixin):
    """员工模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="员工对应的店铺对象")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="员工对应的用户对象")
    roles = models.SmallIntegerField(null=False, default=0, verbose_name="角色，二进制运算进行校验")
    permissions = models.BigIntegerField(null=False, default=0, verbose_name="权限，二进制运算进行校验")
    status = models.SmallIntegerField(
        null=False,
        default=StaffStatus.NORMAL,
        verbose_name="员工状态，0：删除，1：正常",
    )
    position = models.CharField(max_length=16, default="无", verbose_name="员工职位")
    entry_date = models.DateField(auto_now_add=True, verbose_name="员工入职时间")
    remark = models.CharField(max_length=32,default="", verbose_name="备注")

    class Meta:
        db_table = "staff"
        verbose_name = "员工"
        verbose_name_plural = verbose_name


class StaffApply(models.Model, TimeBaseMixin):
    """员工申请表模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="对应的用户对象")
    status = models.SmallIntegerField(
        null=False,
        default=StaffApplyStatus.APPLYING,
        verbose_name="申请状态,0:未申请，1；申请中，2：已通过"
    )
    expired = models.SmallIntegerField(
        null=False,
        default=StaffApplyExpired.NO,
        verbose_name="申请信息是否过期，0：未过期，1：已过期"
    )

    class Meta:
        db_table = "staff_apply"
        verbose_name = "员工申请表"
        verbose_name_plural = verbose_name

