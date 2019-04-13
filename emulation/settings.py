API_URL = 'http://client-api.dlbas.me/'
LOCK_FILE_NAME = '/var/lock/market-platform-emulation-lock'

try:
    from .settings_local import *
except ImportError:
    pass
