cd /root/market-platform/client_api;
pipenv run python manage.py migrate;
systemctl restart client_api.service;
