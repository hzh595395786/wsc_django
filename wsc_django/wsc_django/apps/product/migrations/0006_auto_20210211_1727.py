# Generated by Django 3.1.6 on 2021-02-11 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_auto_20210211_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productgroup',
            name='description',
            field=models.CharField(default='无', max_length=128, verbose_name='商品分组描述'),
        ),
    ]
