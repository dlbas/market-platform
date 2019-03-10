from flask import Flask

from .emulation import run_emulation
from . import settings

app = Flask(__name__)


@app.route('/emulate')
def index():
    # TODO: this
    return run_emulation(
        settings.API_URL,
        generate_users=True
    )
