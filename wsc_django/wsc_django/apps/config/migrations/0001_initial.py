# Generated by Django 3.1.6 on 2021-02-06 08:29

from django.db import migrations, models
import django.db.models.deletion
import wsc_django.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MsgNotify',
            fields=[
                ('id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='shop.shop')),
                ('order_confirm_wx', models.BooleanField(default=False, verbose_name='开始配送/等待自提-微信')),
                ('order_confirm_msg', models.BooleanField(default=False, verbose_name='开始配送/等待自提-短信')),
                ('order_finish_wx', models.BooleanField(default=False, verbose_name='订单完成-微信')),
                ('order_finish_msg', models.BooleanField(default=False, verbose_name='订单完成-短信')),
                ('order_refund_wx', models.BooleanField(default=False, verbose_name='订单退款-微信')),
                ('order_refund_msg', models.BooleanField(default=False, verbose_name='订单退款-短信')),
                ('group_success_wx', models.BooleanField(default=False, verbose_name='成团提醒-微信')),
                ('group_success_msg', models.BooleanField(default=False, verbose_name='成团提醒-短信')),
                ('group_failed_wx', models.BooleanField(default=False, verbose_name='拼团失败-微信')),
                ('group_failed_msg', models.BooleanField(default=False, verbose_name='拼团失败-短信')),
            ],
            options={
                'verbose_name': '消息通知',
                'verbose_name_plural': '消息通知',
                'db_table': 'msgnotfiy',
            },
            bases=(models.Model, wsc_django.utils.models.TimeBaseMixin),
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='shop.shop', verbose_name='一个店铺对应一个小票,就直接绑定')),
                ('bottom_msg', models.CharField(default='', max_length=128, verbose_name='小票底部信息')),
                ('bottom_qrcode', models.CharField(default='', max_length=128, verbose_name='小票底部二维码')),
                ('bottom_image', models.CharField(default='', max_length=512, verbose_name='小票底部图片,预留')),
                ('brcode_active', models.SmallIntegerField(default=0, verbose_name='打印订单号条码')),
                ('copies', models.SmallIntegerField(default=1, verbose_name='小票打印份数')),
            ],
            options={
                'verbose_name': '小票',
                'verbose_name_plural': '小票',
                'db_table': 'receipt',
            },
            bases=(models.Model, wsc_django.utils.models.TimeBaseMixin),
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.SmallIntegerField(default=1, verbose_name='打印机类型1:本地2:云, 预留')),
                ('brand', models.SmallIntegerField(verbose_name='打印机品牌 1:易联云, 2:飞印, 3:佛山喜讯, 4:365 S1, 5:365 S2, 6:森果')),
                ('code', models.CharField(default='', max_length=32, verbose_name='打印机终端号')),
                ('key', models.CharField(default='', max_length=32, verbose_name='打印机秘钥')),
                ('temp_id', models.SmallIntegerField(default=1, verbose_name='打印模板, 预留')),
                ('auto_print', models.SmallIntegerField(default=1, verbose_name='订单自动打印')),
                ('status', models.SmallIntegerField(default=1, verbose_name='打印机状态,预留')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop', verbose_name='打印机对应店铺')),
            ],
            options={
                'verbose_name': '打印机',
                'verbose_name_plural': '打印机',
                'db_table': 'printer',
            },
            bases=(models.Model, wsc_django.utils.models.TimeBaseMixin),
        ),
    ]