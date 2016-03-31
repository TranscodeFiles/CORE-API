#!/bin/bash
set -e

if [ -z "$1" ] || [ "$1" = 'gunicorn' ]; 
then
    echo "Start gunicorn"
    exec gunicorn --config /deploy/gunicorn_config.py --reload coreapi:app
elif [ "$1" = 'worker' ];
then 
    echo "Start worker"
    export C_FORCE_ROOT="true"
    exec celery -A tasks.celery worker
fi
