# Generated by Django 3.1.6 on 2021-03-15 02:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order_num', models.CharField(max_length=20, verbose_name='订单号')),
                ('order_id', models.IntegerField(verbose_name='订单id')),
                ('shop_id', models.IntegerField(verbose_name='商铺id')),
                ('operate_time', models.DateTimeField(auto_now_add=True, verbose_name='操作时间')),
                ('operator_id', models.IntegerField(verbose_name='操作人的user_id')),
                ('operate_type', models.SmallIntegerField(verbose_name='操作类型')),
                ('operate_content', models.CharField(default='', max_length=512, verbose_name='操作内容')),
            ],
            options={
                'verbose_name': '订单日志',
                'verbose_name_plural': '订单日志',
                'db_table': 'order_log',
            },
        ),
    ]
