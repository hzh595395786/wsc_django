# Generated by Django 3.1.6 on 2021-02-23 03:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_auto_20210223_1104'),
        ('product', '0002_auto_20210219_1712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop', verbose_name='货品对应的商铺对象'),
        ),
    ]