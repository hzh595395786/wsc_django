# Generated by Django 3.1.6 on 2021-06-06 12:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('receipt_fee', models.IntegerField(verbose_name='实际支付金额')),
                ('transaction_id', models.CharField(max_length=64, verbose_name='支付交易单号')),
                ('channel_trade_no', models.CharField(max_length=64, verbose_name='支付通道的支付单号')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.order', verbose_name='对应订单对象')),
            ],
            options={
                'verbose_name': '订单在线支付信息',
                'verbose_name_plural': '订单在线支付信息',
                'db_table': 'order_transaction',
            },
        ),
    ]
