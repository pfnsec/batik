FROM python:3.9-slim-bullseye as builder

RUN apt-get update
RUN apt-get install -y build-essential

RUN mkdir /batik_env
RUN python3 -m venv /batik_env

ENV PATH="/batik_env/bin:$PATH"

WORKDIR /batik
COPY ./setup.py /batik/setup.py
COPY ./README.md /batik/README.md

RUN python setup.py egg_info
RUN pip install `grep -v '^\[' *.egg-info/requires.txt`

COPY . /batik

RUN pip install .
