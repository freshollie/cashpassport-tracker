FROM python:3.5

LABEL maintainer="Oliver Bell <freshollie@gmail.com>"
WORKDIR /opt/cashpassport-tracker

COPY setup.py setup.py
RUN python setup.py develop

COPY src/src
