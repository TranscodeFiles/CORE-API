# factory.py
from extensions import celery
from flask_restful import Api
from flask import Flask
from celery import Celery


def create_celery_app():
    app, api = create_app()
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    celery.app = app

    yield celery
    yield app


def create_app():
    app = Flask(__name__)
    api = Api(app)
    app.config.from_object('settings')

    celery.config_from_object(app.config)

    yield app
    yield api
