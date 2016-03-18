# gunicorn-flask

FROM ubuntu:14.04
MAINTAINER Daniel Riti <dmriti@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update 
RUN apt-get install -y software-properties-common
RUN apt-add-repository ppa:mc3man/trusty-media
RUN apt-get update 
RUN apt-get install -y ffmpeg
RUN apt-get install -y python python-pip python-virtualenv

# Setup flask application
RUN mkdir -p /deploy/app
COPY gunicorn_config.py /deploy/gunicorn_config.py
COPY app /deploy/app
RUN pip install -r /deploy/app/requirements.txt
WORKDIR /deploy/app

EXPOSE 5000

# Start gunicorn
CMD ["gunicorn", "--config", "/deploy/gunicorn_config.py","--reload", "core-api:app"]

