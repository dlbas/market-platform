#!/usr/bin/env bash
set -e

if [[ -z $EMULATION_HOST ]]; then
    EMULATION_HOST="0.0.0.0"
    echo "Running emulation on default host $EMULATION_HOST"
else
    echo "Running emulation on EMULATION_HOST=$EMULATION_HOST"
fi

if [[ -z $EMULATION_PORT ]]; then
    EMULATION_PORT="5000"
    echo "Running emulation on default port $EMULATION_PORT"
else
    echo "Running emulation on EMULATION_PORT=$EMULATION_PORT"
fi

if [[ $1 == run ]]; then
    python -m flask run --host ${EMULATION_HOST} --port ${EMULATION_PORT}
else
    exec "$@"
fi



