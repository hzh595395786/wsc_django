# Generated by Django 3.1.6 on 2021-02-11 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_auto_20210206_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productgroup',
            name='description',
            field=models.CharField(max_length=128, null=True, verbose_name='商品分组描述'),
        ),
    ]