DEBUG = True

CELERY_BROKER_URL = 'amqp://guest:guest@rabbit:5672//'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@rabbit:5672//'

CEPH_SWIFT_USER = 'johndoe:swift'
CEPH_SWIFT_KEY = 'dUJKqgcL5UBRIeHFjErpU7MayWhAyE0YjXnbmjKY'
CEPH_SWIFT_AUTHURL = 'http://10.0.2.15/auth'
