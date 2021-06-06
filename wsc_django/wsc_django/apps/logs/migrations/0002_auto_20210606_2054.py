# Generated by Django 3.1.6 on 2021-06-06 12:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('logs', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='stafflog',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
        migrations.AddField(
            model_name='promotionlog',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
        migrations.AddField(
            model_name='productlog',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
        migrations.AddField(
            model_name='orderlog',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
        migrations.AddField(
            model_name='operatelogunify',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
        migrations.AddField(
            model_name='configlog',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人'),
        ),
    ]