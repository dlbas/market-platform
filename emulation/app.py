import json

from flask import Flask, request, Response
from multiprocessing import Process

from .emulation import run_emulation
from .tokenization import tokenize
from . import settings

app = Flask(__name__)


@app.route('/emulate', methods=['GET', 'POST'])
def index():
    # TODO: this
    data = json.loads(request.data)
    number_of_token_bags = tokenize(
        PD=data.get('PD'),
        LGD=data.get('LGD'),
        credit_value=data.get('creditSum', 100),
        number_of_credits=data.get('creditsCount')
    )

    p = Process(target=run_emulation, kwargs=dict(
        assets=number_of_token_bags,
        days=data.get('days'),
        yearreturn=data.get('placementRate'),
        nplaysers=3)  # TODO: hardcode
    )
    p.start()
    # run_emulation(**dict(
    #     assets=number_of_token_bags,
    #     days=data.get('days'),
    #     yearreturn=data.get('placementRate'),
    #     nplaysers=3))  # TODO: hardcode
    return Response(status=200)
