# gunicorn-flask

FROM ubuntu:14.04
MAINTAINER Aymeric Daurelle <aymeric42680@gmail.com>

EXPOSE 5001

ENV DEBIAN_FRONTEND noninteractive

COPY gunicorn_config.py /deploy/gunicorn_config.py
COPY app /deploy/app
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-add-repository ppa:mc3man/trusty-media && \
    apt-get update && \
    apt-get install -y ffmpeg python python-pip python-virtualenv && \
    mkdir -p /deploy/app && \
    pip install -r /deploy/app/requirements.txt && \
    chmod +x /docker-entrypoint.sh && \
    apt-get clean

ENTRYPOINT ["/docker-entrypoint.sh"]

WORKDIR /deploy/app
