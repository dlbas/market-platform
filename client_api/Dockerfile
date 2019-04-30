# Client api image
FROM python:3.6-alpine

RUN apk --no-cache add \
     bash \
     gcc \
     musl-dev \
     python3-dev \
     postgresql-dev

WORKDIR ..

EXPOSE 8000

COPY Pipfile .
COPY Pipfile.lock .

RUN pip install pipenv && pipenv sync


# actually copy files in separate lines is considered a good practice
# because when Docker builds the image one more time it will check every file atomically and recreate the layers
# only if needed
ENV PYTHONUNBUFFERED 1
COPY client_api/manage.py .
COPY client_api/client_api client_api/
COPY client_api/client_user client_user/
COPY client_api/entrypoint.sh .


ENTRYPOINT ["./entrypoint.sh"]
CMD ["runserver"]
