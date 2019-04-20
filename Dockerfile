# Client api image
FROM python:3.6-alpine

EXPOSE 8000

ENV PYTHONUNBUFFERED 1
COPY Pipfile .
COPY Pipfile.lock .
COPY client_api client_api/
COPY entrypoint.sh .

RUN apk --no-cache add \
     bash \
     build-base \
     libffi-dev \
     linux-headers \
     musl-dev \
     postgresql-dev

RUN pip install pipenv
RUN pipenv sync


ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

