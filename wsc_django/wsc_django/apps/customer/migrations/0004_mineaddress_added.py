# Generated by Django 3.1.6 on 2021-06-08 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0003_auto_20210606_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='mineaddress',
            name='added',
            field=models.CharField(max_length=50, null=True, verbose_name='补充说明，可以填写门牌号等信息'),
        ),
    ]