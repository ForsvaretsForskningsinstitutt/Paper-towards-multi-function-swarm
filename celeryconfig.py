BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = "amqp"

ENV_PYTHON="/usr/bin/python"

CELERY_IMPORTS = ('tasks',)

CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_IGNORE_RESULT = False
CELERY_RESULT_PERSISTENT = False
WORKER_MAX_TASKS_PER_CHILD=10
WORKER_MAX_MEMORY_PER_CHILD=150000
WORKER_PREFETCH_MULTIPLIER=1

BROKER_CONNECTION_MAX_RETRIES = 1


CELERY_TIMEZONE = 'Europe/Oslo'
CELERY_ENABLE_UTC = True
CELERY_DISABLE_RATE_LIMITS = True
CELERY_TASK_RESULT_EXPIRES=3600
