API_URL = 'http://localhost:8000/'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
LOCK_FILE_NAME = '/var/lock/market-platform-emulation-lock'

try:
    from .settings_local import *
except ImportError:
    pass

try:
    from .settings_docker import *
except ImportError:
    pass
