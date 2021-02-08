# Generated by Django 3.1.6 on 2021-02-08 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_auto_20210208_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shop',
            name='shop_city',
            field=models.IntegerField(default=0, verbose_name='店铺所在城市编号'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='shop_county',
            field=models.IntegerField(default=0, verbose_name='店铺所在国家编号'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='shop_province',
            field=models.IntegerField(default=0, verbose_name='店铺所在省份编号'),
        ),
    ]
