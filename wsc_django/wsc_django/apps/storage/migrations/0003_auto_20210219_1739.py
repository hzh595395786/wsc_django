# Generated by Django 3.1.6 on 2021-02-19 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_productstoragerecord_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productstoragerecord',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='货品库存变更记录创建时间'),
        ),
    ]