# Generated by Django 3.1.6 on 2021-06-06 12:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='super_admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='商铺老板'),
        ),
        migrations.AddField(
            model_name='paychannel',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop', verbose_name='店铺对象'),
        ),
        migrations.AddIndex(
            model_name='shop',
            index=models.Index(fields=['shop_code'], name='ux_shop_code'),
        ),
        migrations.AddIndex(
            model_name='shop',
            index=models.Index(fields=['super_admin'], name='ix_super_admin'),
        ),
    ]
