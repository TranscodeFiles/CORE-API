#!/bin/bash
set -e

if [ -z "$1" ] || [ "$1" = 'gunicorn' ]; 
then
    echo "Start gunicorn"
    exec gunicorn --config /deploy/gunicorn_config.py --reload core-api:app
elif [ "$1" = 'worker' ];
then 
    echo "Start worker"
    exec celery -A core-api:app  worker
fi
