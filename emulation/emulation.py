import numpy as np
import requests
import json
import math
import logging

import settings

LOGGING_FORMAT = '%(asctime)-15s %(user)s %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


class AccessTokensFileNotFound(Exception):
    pass

def create_users(url, players):
    '''Создаем юзеровна серваке'''
    for i in players:
        resp = requests.post(url + 'api/v1/user/create-user/',
                             headers={'Content-type': 'application/json'},
                             json={'email': i.email, 'password': i.password})
        if resp.status_code != 201:
            logger.warning(f'user {i.email} already exists')


def get_tokens(url, players):
    '''Получаем токены c сервера'''
    for i in players:
        i.token = requests.post(url + 'api/v1/user/api-token-auth/',
                                json={'email': i.email, 'password': i.password}).json()['token']


def dump_tokens(filename, players):
    '''Загрузка токентов в файл'''
    dic = {}

    for n, pl in enumerate(players):
        dic[n] = pl.token
    with open(filename, 'w') as outfile:
        json.dump(dic, outfile)


def load_tokens(filename, players, num):
    '''Загружаем токены из файла'''
    with open(filename, 'r') as file:
        tokens = json.load(file)
    for i in range(num):
        players[i].token = tokens[str(i)]


def delete_orders(url, bank):
    return requests.delete(url + 'api/v1/user/orders/delete-all/', headers={'Authorization': 'JWT ' + bank.token})


class Person:

    def __init__(self, email, targetreturn=0.12, money=100, sellp=.2, buyp=.2, skipp=.2, assets=0,
                 maxproportion=0.5, minproportion=0.1):
        self.email = email
        self.password = 'abc123PPHUILA'
        self.token = ''
        self.curmoney = money
        self.curassets = assets
        self.targetreturn = targetreturn
        self.curreturn = 0
        self.assets, self.money = [], []
        self.assets.append(self.curassets)
        self.money.append(self.curmoney)
        self.maxproportion, self.minproportion = maxproportion, minproportion
        self.buyp, self.skipp, self.sellp = buyp, skipp, sellp

    def action(self, url, assetreturn):
        buy, sell = self.buyp, self.sellp
        deltareturn = self.targetreturn - self.curreturn
        if deltareturn >= 0:
            buy = buy + (deltareturn) / self.targetreturn * (1 - self.skipp - self.buyp - self.sellp)
        else:
            sell = sell - deltareturn / self.curreturn * (1 - self.skipp - self.buyp - self.sellp)
        rnd = np.random.uniform()
        if rnd <= buy:
            return self.place_buy(url, deltareturn, assetreturn)
        elif rnd <= buy + sell:
            return self.place_sell(url, deltareturn, assetreturn)
        else:
            return self.skip()

    def skip(self):
        return {'type': 'skip', 'remaining_sum': 0, 'price': 0, 'status': 0}

    def sell(self, deltareturn, assetreturn):
        proportion = self.minproportion - np.minimum(deltareturn / \
                                                     np.maximum(self.targetreturn, self.curreturn) * (
                                                             self.maxproportion - self.minproportion), 0)
        rtrn = assetreturn * (1 - np.sign(deltareturn) * 0.01 * np.random.exponential(np.abs(deltareturn /
                                                                                             np.maximum(
                                                                                                 self.targetreturn,
                                                                                                 self.curreturn))))
        price = 1 / (1 + rtrn)
        return (proportion * self.curassets, rtrn, price)

    def buy(self, deltareturn, assetreturn):
        proportion = self.minproportion + \
                     np.maximum(deltareturn / np.maximum(self.targetreturn, self.curreturn) * \
                                (self.maxproportion - self.minproportion), 0)
        rtrn = assetreturn * (1 + np.sign(deltareturn) * 0.01 * np.random.exponential(np.abs(deltareturn /
                                                                                             np.maximum(
                                                                                                 self.targetreturn,
                                                                                                 self.curreturn))))
        price = 1 / (1 + rtrn)
        return (proportion * self.curmoney, rtrn, price)

    def update_curretrun(self):
        self.curreturn = (self.curmoney + self.curassets) / self.money[0]

    def put_balance(self, url):
        id = requests.get(url + 'api/v1/user/instrument-balance/',
                          headers={'Authorization': 'JWT ' + self.token}).json()[0]['id']
        requests.put(url + 'api/v1/user/instrument-balance/' + str(id),
                     json={'amount': self.curassets}, headers={'Authorization': 'JWT ' + self.token}).json()
        id = requests.get(url + 'api/v1/user/fiat-balance/',
                          headers={'Authorization': 'JWT ' + self.token}).json()['id']
        requests.put(url + 'api/v1/user/fiat-balance/' + str(id),
                     json={'amount': self.curmoney}, headers={'Authorization': 'JWT ' + self.token}).json()

    def update_balance(self, url):
        self.curassets = requests.get(url + 'api/v1/user/instrument-balance/',
                                      headers={'Authorization': 'JWT ' + self.token}).json()[0]['amount']
        self.assets.append(self.curassets)
        self.curmoney = requests.get(url + 'api/v1/user/fiat-balance/',
                                     headers={'Authorization': 'JWT ' + self.token}).json()['amount']
        self.money.append(self.curmoney)
        self.curreturn = (self.curmoney + self.curassets - self.money[0]) / self.money[0]

    def place_buy(self, url, deltareturn, assetreturn):
        amount, assetreturn, price = self.buy(deltareturn, assetreturn)
        return requests.post(url + 'api/v1/user/orders/', headers={'Authorization': 'JWT ' + self.token},
                             json={'type': 'buy', 'price': math.floor(price * 1e4) / 1e4,
                                   'total_sum': math.floor(amount * 1e4) / 1e4,
                                   'expires_in': 4, 'instrument_id': 2}).json()

    def place_sell(self, url, deltareturn, assetreturn):
        amount, assetreturn, price = self.sell(deltareturn, assetreturn)
        return requests.post(url + 'api/v1/user/orders/', headers={'Authorization': 'JWT ' + self.token},
                             json={'type': 'sell', 'price': math.floor(price * 1e4) / 1e4,
                                   'total_sum': math.floor(amount * 1e4) / 1e4,
                                   'expires_in': 4, 'instrument_id': 2}).json()

    def info(self):
        logger.info('Cur money: ', self.curmoney, ' Cur assets: ', self.curassets, ' Target return: ',
                    self.targetreturn,
                    ' Cur return: ', self.curreturn)


class Bank:

    def __init__(self, email="bank@mail.ru", assets=1000, money=0):
        self.curassets = assets
        self.curmoney = money
        self.assets, self.money = [], []
        self.assets.append(self.curassets)
        self.money.append(self.curmoney)
        self.token = 0
        self.email = email
        self.password = "abc123PPHUILA"

    def put_balance(self, url):
        idbank = requests.get(url + 'api/v1/user/instrument-balance/',
                              headers={'Authorization': 'JWT ' + self.token}).json()[0]['id']
        requests.put(url + 'api/v1/user/instrument-balance/' + str(idbank),
                     json={'amount': self.curassets}, headers={'Authorization': 'JWT ' + self.token}).json()
        idbank = requests.get(url + 'api/v1/user/fiat-balance/',
                              headers={'Authorization': 'JWT ' + self.token}).json()['id']
        requests.put(url + 'api/v1/user/fiat-balance/' + str(idbank),
                     json={'amount': self.curmoney}, headers={'Authorization': 'JWT ' + self.token}).json()

    def place_order(self, url, curreturn):
        curprice = 1 / (1 + curreturn)
        return requests.post(url + 'api/v1/user/orders/', headers={'Authorization': 'JWT ' + self.token},
                             json={'type': 'sell', 'price': math.floor(curprice * 1e4) / 1e4,
                                   'total_sum': math.floor(self.curassets * 1e4) / 1e4,
                                   'expires_in': 4, 'instrument_id': 2}).json()

    def update_balance(self, url):
        self.curassets = requests.get(url + 'api/v1/user/instrument-balance/',
                                      headers={'Authorization': 'JWT ' + self.token}).json()[0]['amount']
        self.assets.append(self.curassets)
        self.curmoney = requests.get(url + 'api/v1/user/fiat-balance/',
                                     headers={'Authorization': 'JWT ' + self.token}).json()['amount']
        self.money.append(self.curmoney)

    def create(self, url):
        requests.post(url + 'api/v1/user/create-user/',
                      headers={'Content-type': 'application/json'},
                      json={'email': self.email, 'password': self.password})

    def get_token(self, url):
        self.token = requests.post(url + 'api/v1/user/api-token-auth/',
                                   json={'email': self.email, 'password': self.password}).json()['token']


def dump_info(filename, players, bank):
    dic = {}
    dic['bank_'] = [bank.assets, bank.money]
    for i in players:
        dic[i.email] = [i.assets, i.money]
    with open(filename, 'w') as outfile:
        json.dump(dic, outfile)


def emulate(url=None, duration=None, yearreturn=None, bank=None, peoples=None):
    keys = ['type', 'remaining_sum', 'price', 'status']
    for i in range(duration):
        delete_orders(url, bank)
        logger.info('\n\nDay ', i)
        curreturn = (duration / 365) * (yearreturn - yearreturn / duration * i)
        perm = np.random.permutation(len(peoples))
        money, assets = 0, 0

        if bank.curassets >= 0:
            logger.info('Bank order')
            order = bank.place_order(url, 1.1 * curreturn)
            for k in keys:
                logger.info(order[k], end=' ')

        for ind in perm:
            order = peoples[ind].action(url, curreturn)
            logger.info('\nOrder #', ind)
            for k in keys:
                logger.info(order[k], end=' ')

        for player in peoples:
            player.update_balance(url)
            player.info()
            money += player.curmoney
            assets += player.curassets

        bank.update_balance(url)
        money += bank.curmoney
        assets += bank.curassets
        logger.info('Bank money:', bank.curmoney, ' Bank assets: ', bank.curassets)
        logger.info('Money:', money, ' Assets: ', assets)


def run_emulation(url='http://client-api.dlbas.me/', days=50, yearreturn=.15, nplaysers=10, meanmoney=100, assets=800,
                  meantargetreturn=.15, generate_users=False):
    # Создали объектов
    num = nplaysers
    days = days
    peoples = []
    bank = Bank(assets=assets)
    url = url
    bank.get_token(url)
    for i in range(num):
        email = "bot" + str(i) + "@mail.ru"
        targetreturn = meantargetreturn * days / 365
        target = math.floor(np.random.normal(targetreturn, .4 * targetreturn) * 1e3) / 1e3
        money = math.floor(np.random.normal(meanmoney, 0.3 * meanmoney) * 1e3) / 1e3
        peoples.append(Person(email, target, money=money))
    if generate_users:
        create_users(url, peoples)
        get_tokens(url, peoples)
    else:
        # TODO: get users from file
        try:
            load_tokens(settings.ACCESS_TOKENS_FILE, players=peoples, num=num)
        except FileNotFoundError as e:
            logger.error(e)
            raise AccessTokensFileNotFound(settings.ACCESS_TOKENS_FILE)
    for i in peoples:
        i.put_balance(url)
    bank.put_balance(url)

    emulate(url=url, duration=days, yearreturn=yearreturn, bank=bank, peoples=peoples)


if __name__ == '__main__':
    run_emulation()
