# Generated by Django 3.1.6 on 2021-06-06 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryRealName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('realname', models.CharField(max_length=32, verbose_name='历史真实姓名')),
            ],
            options={
                'verbose_name': '商铺创建者历史真实姓名',
                'verbose_name_plural': '商铺创建者历史真实姓名',
                'db_table': 'history_realname',
            },
        ),
        migrations.CreateModel(
            name='PayChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('smerchant_no', models.CharField(default='', max_length=15, verbose_name='商户号')),
                ('smerchant_name', models.CharField(default='', max_length=100, verbose_name='商户名')),
                ('smerchant_type_id', models.CharField(default='', max_length=15, verbose_name='商户类别id')),
                ('smerchant_type_name', models.CharField(default='', max_length=81, verbose_name='商户类别名')),
                ('pos_id', models.CharField(default='', max_length=9, verbose_name='柜台号')),
                ('terminal_id1', models.CharField(default='', max_length=50, verbose_name='终端号1')),
                ('terminal_id2', models.CharField(default='', max_length=50, verbose_name='终端号2')),
                ('access_token', models.CharField(default='', max_length=32, verbose_name='扫呗access_token')),
                ('clearing_rate', models.FloatField(default=2.8, verbose_name='商户的清算费率,利楚默认是千分之2.8，建行是0')),
                ('clearing_account_id', models.IntegerField(default=0, verbose_name='商户的清算账号ID')),
                ('channel_type', models.SmallIntegerField(default=0, verbose_name='支付渠道, 1:利楚, 2:建行')),
                ('pub_key', models.CharField(max_length=500, verbose_name='账户公匙')),
                ('province', models.CharField(default='Hubei', max_length=32, verbose_name='用户所在省份')),
            ],
            options={
                'verbose_name': '支付渠道',
                'verbose_name_plural': '支付渠道',
                'db_table': 'pay_channel',
            },
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('status', models.SmallIntegerField(default=2, verbose_name='商铺状态 0: 已关闭 1: 正常,审核通过, 2: 审核中, 3: 已拒绝')),
                ('shop_name', models.CharField(max_length=128, verbose_name='商铺名称')),
                ('shop_code', models.CharField(default='', max_length=16, verbose_name='随机字符串，用于代替id')),
                ('shop_phone', models.CharField(default='', max_length=32, verbose_name='联系电话')),
                ('shop_img', models.CharField(default='', max_length=300, verbose_name='门头照片')),
                ('business_licence', models.CharField(default='', max_length=300, verbose_name='营业执照')),
                ('shop_address', models.CharField(default='', max_length=100, verbose_name='商铺地址')),
                ('shop_county', models.IntegerField(default=0, verbose_name='商铺所在国家编号')),
                ('shop_province', models.IntegerField(default=0, verbose_name='商铺所在省份编号')),
                ('shop_city', models.IntegerField(default=0, verbose_name='商铺所在城市编号')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='商铺创建时间')),
                ('description', models.CharField(default='', max_length=256, verbose_name='商铺描述')),
                ('inviter_phone', models.CharField(default='', max_length=32, verbose_name='推荐人手机号')),
                ('cerify_active', models.SmallIntegerField(default=1, verbose_name='是否认证,1:是,0:否')),
                ('shop_verify_type', models.SmallIntegerField(default=1, verbose_name='商铺类型,0:企业,1:个人')),
                ('shop_verify_content', models.CharField(max_length=200, verbose_name='认证内容(公司名称)')),
                ('pay_active', models.SmallIntegerField(default=1, verbose_name='是否开通线上支付,1:是,0:否')),
            ],
            options={
                'verbose_name': '商铺',
                'verbose_name_plural': '商铺',
                'db_table': 'shop',
            },
        ),
        migrations.CreateModel(
            name='ShopRejectReason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('reject_reason', models.CharField(default='', max_length=256, verbose_name='拒绝理由')),
            ],
            options={
                'verbose_name': '商铺拒绝理由',
                'verbose_name_plural': '商铺拒绝理由',
                'db_table': 'shop_reject_reason',
            },
        ),
    ]
