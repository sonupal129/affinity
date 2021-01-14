FROM python:3

ENV PYTHONUNBUFFERED 1 

WORKDIR /app

ADD . /app

COPY . /app

RUN pip install -r requirements.txt