# Generated by Django 3.1.6 on 2021-03-12 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20210313_0407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdetail',
            name='refund_type',
            field=models.SmallIntegerField(null=True, verbose_name='退款方式,同order'),
        ),
    ]
