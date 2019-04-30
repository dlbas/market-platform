#!/usr/bin/env bash
set -e

if [[ -z $CLIENT_API_HOST ]]; then
    CLIENT_API_HOST="0.0.0.0"
    echo "Running client-api on default host $CLIENT_API_HOST"
else
    echo "Running client-api on CLIENT_API_HOST=$CLIENT_API_HOST"
fi

if [[ -z $CLIENT_API_PORT ]]; then
    CLIENT_API_PORT="8000"
    echo "Running client-api on default port $CLIENT_API_HOST"
else
    echo "Running client-api on CLIENT_API_PORT=$CLIENT_API_PORT"
fi

if [[ $1 == 'runserver' ]]; then
    pipenv run python ./manage.py migrate --noinput && \
    pipenv run python ./manage.py runserver ${CLIENT_API_HOST}:${CLIENT_API_PORT}
else
    exec "$@"
fi


