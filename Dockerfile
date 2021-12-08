FROM python:3.9-alpine as base

#RUN apk add build-base libffi-dev openssl-dev yaml-dev

WORKDIR /_batik
COPY . /_batik

RUN pip install .
