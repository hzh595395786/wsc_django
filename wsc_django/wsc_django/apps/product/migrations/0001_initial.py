# Generated by Django 3.1.6 on 2021-02-24 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=64, verbose_name='货品名称')),
                ('name_acronym', models.CharField(max_length=64, verbose_name='货品名称拼音')),
                ('price', models.DecimalField(decimal_places=4, max_digits=13, verbose_name='货品单价')),
                ('storage', models.DecimalField(decimal_places=4, default=0, max_digits=13, verbose_name='货品库存')),
                ('code', models.CharField(default='', max_length=32, verbose_name='货品编码')),
                ('summary', models.CharField(default='', max_length=128, verbose_name='货品简介')),
                ('cover_image_url', models.CharField(default='', max_length=512, verbose_name='货品封面图')),
                ('description', models.TextField(default='', verbose_name='货品详情描述')),
                ('status', models.SmallIntegerField(default=1, verbose_name='货品状态, 0:删除, 1:上架, 2:下架')),
            ],
            options={
                'verbose_name': '货品',
                'verbose_name_plural': '货品',
                'db_table': 'prodoct',
            },
        ),
        migrations.CreateModel(
            name='ProductPicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image_url', models.CharField(max_length=512, verbose_name='货品轮播图url')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.product', verbose_name='对应货品对象')),
            ],
            options={
                'verbose_name': '货品轮播图',
                'verbose_name_plural': '货品轮播图',
                'db_table': 'prodoct_picture',
            },
        ),
        migrations.CreateModel(
            name='ProductGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=32, verbose_name='商品分组名称')),
                ('description', models.CharField(default='无', max_length=128, verbose_name='商品分组描述')),
                ('sort', models.IntegerField(null=True, verbose_name='商品分组排序')),
                ('level', models.SmallIntegerField(null=True, verbose_name='商品分组级别')),
                ('default', models.SmallIntegerField(default=0, verbose_name='是否为默认分组, 0:否,1:是')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.productgroup', verbose_name='该商品分组的父级ID')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop', verbose_name='对应的店铺对象')),
            ],
            options={
                'verbose_name': '货品分组',
                'verbose_name_plural': '货品分组',
                'db_table': 'prodoct_group',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productgroup', verbose_name='货品分组ID'),
        ),
        migrations.AddField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop', verbose_name='货品对应的商铺对象'),
        ),
    ]
