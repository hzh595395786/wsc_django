# Generated by Django 3.1.6 on 2021-02-19 09:12

from django.db import migrations, models
import django.db.models.deletion
import wsc_django.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateField(auto_now_add=True, verbose_name='下单日期')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='下单时间')),
                ('delivery_method', models.SmallIntegerField(default=1, verbose_name='配送方式,1:送货上门,2:客户自提')),
                ('delivery_period', models.CharField(max_length=32, verbose_name='自提处理时段')),
                ('order_num', models.CharField(max_length=20, unique=True, verbose_name='订单号')),
                ('order_status', models.SmallIntegerField(default=1, verbose_name='订单状态,具体见constant')),
                ('remark', models.CharField(default='', max_length=64, verbose_name='订单备注')),
                ('pay_type', models.SmallIntegerField(default=2, verbose_name='订单支付方式')),
                ('order_type', models.SmallIntegerField(default=1, verbose_name='订单类型,1:普通订单，2：拼团订单')),
                ('amount_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='货款金额（优惠前）')),
                ('amount_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='货款金额（优惠后）')),
                ('delivery_amount_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='货款金额运费（优惠前）')),
                ('delivery_amount_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='货款金额运费（优惠后）')),
                ('total_amount_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='订单金额（优惠前）')),
                ('total_amount_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='订单金额（优惠后）')),
                ('refund_type', models.SmallIntegerField(default=2, verbose_name='订单退款方式')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'db_table': 'order',
            },
            bases=(models.Model, wsc_django.utils.models.TimeBaseMixin),
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateField(auto_now_add=True, verbose_name='下单日期')),
                ('quantity_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='量（优惠前）')),
                ('quantity_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='量（优惠后）')),
                ('price_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='单价（优惠前）')),
                ('price_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='单价（优惠后）')),
                ('amount_gross', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='金额（优惠前）')),
                ('amount_net', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='金额（优惠后）')),
                ('status', models.SmallIntegerField(verbose_name='订单状态,同order')),
                ('pay_type', models.SmallIntegerField(verbose_name='支付方式,同order')),
                ('refund_type', models.SmallIntegerField(verbose_name='退款方式,同order')),
                ('promotion_type', models.SmallIntegerField(default='', verbose_name='活动类型（预留）')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.customer', verbose_name='订单对应客户对象')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.order', verbose_name='对应的订单对象')),
            ],
            options={
                'verbose_name': '订单详情',
                'verbose_name_plural': '订单详情',
                'db_table': 'order_detail',
            },
            bases=(models.Model, wsc_django.utils.models.TimeBaseMixin),
        ),
    ]
