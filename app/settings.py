DEBUG = True

CELERY_BROKER_URL = 'amqp://guest:guest@rabbit:5672//'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@rabbit:5672//'
