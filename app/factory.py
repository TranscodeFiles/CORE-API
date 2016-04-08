from extensions import celery
from flask_restful import Api
from flask import Flask
from celery import Celery


def create_celery_app():
    """
    Create celery app
    :return: celery app and app
    """
    app, api = create_app()
    app_celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    app_celery.conf.update(app.config)
    task_base = app_celery.Task

    class ContextTask(task_base):
        """Set context for celery"""
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return task_base.__call__(self, *args, **kwargs)

    app_celery.Task = ContextTask
    app_celery.app = app

    yield app_celery
    yield app


def create_app():
    """
    Create app flask and flask api
    :return: app and app api
    """
    app = Flask(__name__)
    api = Api(app)
    app.config.from_object('settings')

    celery.config_from_object(app.config)

    yield app
    yield api
