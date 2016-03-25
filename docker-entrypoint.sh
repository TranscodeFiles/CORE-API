#!/bin/bash
set -e

if [ -z "$1" ] || [ "$1" = 'gunicorn' ]; 
then
    echo "Start gunicorn"
    exec gunicorn --config /deploy/gunicorn_config.py --reload coreapi:app
elif [ "$1" = 'worker' ];
then 
    echo "Start worker"
    exec celery -A coreapi:app  worker
fi
