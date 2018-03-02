FROM python:2

WORKDIR /opt/cashpassport-tracker

COPY src/src
COPY setup.py setup.py

RUN python setup.py develop

CMD python src/tracker.py
