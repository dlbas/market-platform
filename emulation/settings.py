import os

API_URL = 'http://localhost:8000/'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
LOCK_FILE_NAME = '/var/lock/market-platform-emulation-lock'

try:
    from settings_local import *

    print(
        f'Found settings local. API: {API_URL}, REDIS_HOST: {REDIS_HOST}, REDIS_PORT: {REDIS_PORT}'
    )
except ImportError:
    pass

if os.environ.get('DOCKER'):
    try:
        from settings_docker import *

        print(
            f'Found settings docker. API: {API_URL}, REDIS_HOST: {REDIS_HOST}, REDIS_PORT: {REDIS_PORT}'
        )
    except ImportError:
        print('Can not find docker settings')
