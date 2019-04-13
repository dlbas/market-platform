import json
import fcntl
import logging

from flask import Flask, request, Response
from multiprocessing import Process

from .emulation import run_emulation
from .tokenization import tokenize
from . import settings

app = Flask(__name__)

process = None  # made process a global to avoid zombie process

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)


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
    process = Process(target=run_emulation, kwargs=dict(
        assets=number_of_token_bags,
        meanmoney=data.get('meanmoney', 800),
        days=data.get('days'),
        yearreturn=data.get('placementRate'),
        meantargetreturn=data.get('placementRate'),
        nplaysers=3)  # TODO: hardcode
                      )
    process.start()
    return Response(status=200)


@app.route('/results', methods=['GET'])
def results():
    """
    Listens for incoming GET request and returns emulation statistics (TBA)
    :return:
    """
    with open(settings.LOCK_FILE_NAME, 'w') as lockfile:
        if has_flock(lockfile):
            return Response(status=503)
    #  TODO: this
    return Response(status=200)
