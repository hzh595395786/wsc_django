import os
from celery import Celery
from django.conf import settings

# 设置环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# 创建celery应用
app = Celery('wsc_django', backend="")
app.config_from_object('celery_tasks.config')

# 如果在工程的应用中创建了tasks.py模块，那么Celery应用就会自动去检索创建的任务。比如你添加了一个任#务，在django中会实时地检索出来。
app.autodiscover_tasks(['celery_tasks.celery_auto_word'])