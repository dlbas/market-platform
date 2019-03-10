API_URL = 'http://client-api.dlbas.me/'
ACCESS_TOKENS_FILE = 'tokens.json'

try:
    from .settings_local import *
except ImportError:
    pass
