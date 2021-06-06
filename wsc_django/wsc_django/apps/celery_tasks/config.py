from kombu import Exchange, Queue


timezone = 'Asia/Shanghai'  # 任务时区
CELERY_BROKER = "amqp://guest@localhost:5672//"  # broker
task_soft_time_limit = 600,  # 任务超时时间
CELERY_CONCURRENCY = 4  # 任务并发数
worker_disable_rate_limits = True  # 任务频率限制开关
task_queues = (    #设置add队列,绑定routing_key
    Queue('wsc_auto_work', Exchange("wsc_auto_work"), routing_key='wsc_auto_work'),
)
task_routes = {
    "auto_cancel_order": {
        'queue': 'wsc_auto_work',
        'routing_key': 'wsc_auto_work',
    },
    "auto_publish_groupon": {
        'queue': 'wsc_auto_work',
        'routing_key': 'wsc_auto_work',
    },
    "auto_expire_groupon": {
        'queue': 'wsc_auto_work',
        'routing_key': 'wsc_auto_work',
    },
    "auto_fail_groupon_attend": {
        'queue': 'wsc_auto_work',
        'routing_key': 'wsc_auto_work',
    },
    "auto_validate_groupon_attend": {
        'queue': 'wsc_auto_work',
        'routing_key': 'wsc_auto_work',
    }
}