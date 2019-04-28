import json
import fcntl
import logging
import requests
import uuid

import redis as _redis

from flask import Flask, request, Response
from multiprocessing import Process

from .emulation import run_emulation
from tokenization import tokenize
import settings

app = Flask(__name__)

process = None  # made process a global to avoid zombie process

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)

redis = _redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


def has_flock(fd):
    """
    Checks if fd has flock over it
    True if it is, False otherwise
    :param fd:
    :return:
    :rtype: bool
    """
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    else:
        return False


def has_redis_lock(uuid):
    """
    Checks if redis has lock on uuid
    :param uuid:
    :return:
    """
    try:
        with redis.lock(str(uuid) + '__lock'):
            pass
    except _redis.exceptions.LockError:
        return True
    else:
        return False


@app.route('/emulate', methods=['POST'])
def emulate():
    """
    Listens for incoming POST request with emulation parameters
    :return:
    """
    # TODO: this
    data = json.loads(request.data)
    number_of_token_bags = tokenize(
        PD=data.get('PD'),
        LGD=data.get('LGD'),
        credit_value=data.get('creditSum', 100),
        number_of_credits=data.get('creditsCount')
    )

    with open(settings.LOCK_FILE_NAME, 'w') as lockfile:
        if has_flock(lockfile):
            logger.warning('Could not acquire lock.')
            return Response(status=503)
    global process
    if process is not None:
        process.join()  # to avoid zombie process
    emulation_uuid = uuid.uuid4()

    redis.set(str(emulation_uuid) + '__token_bags', number_of_token_bags)

    process = Process(target=run_emulation,
                      kwargs=dict(
                          url=settings.API_URL,
                          emulation_uuid=emulation_uuid,
                          assets=number_of_token_bags,
                          meanmoney=data.get('meanmoney', 800),
                          days=data.get('days'),
                          yearreturn=data.get('placementRate'),
                          meantargetreturn=data.get('placementRate'),
                          nplaysers=data.get('peopleCount', 10)
                      )
                      )
    process.start()
    return Response(
        json.dumps({'result': {'emulation_uuid': str(emulation_uuid)}}),
        status=200,
        content_type='application/json'
    )


@app.route('/results', methods=['GET'])
def results():
    """
    Listens for incoming GET request and returns emulation statistics (TBA)
    :return:
    """
    emulation_uuid = request.args.get('uuid')
    if not emulation_uuid:
        return Response(status=404)
    if has_redis_lock(emulation_uuid):
        return Response(status=503)

    data = requests.get(settings.API_URL + 'api/v1/user/stats/',
                        params={'uuid': emulation_uuid}).json()

    initial_token_bags = redis.get(str(emulation_uuid) + '__token_bags')

    data['result']['placement_stats'] = [v / float(initial_token_bags) for v in
                                         data['result']['placement_stats']]

    return Response(json.dumps(data), status=200,
                    content_type='application/json')
