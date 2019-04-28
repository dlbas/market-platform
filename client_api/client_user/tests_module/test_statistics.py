from django.test import TestCase

from client_user import models
from client_user.tests_module.utils import Fixtures


class BaseTestCase(TestCase):
    def setUp(self):
        self.user1 = Fixtures.create_user('pes@mail.ru', 0)
        self.user2 = Fixtures.create_user('psina@mail.ru', 0)
        self.bank = Fixtures.create_user('bank1@mail.ru', 500)
        self.instrument = Fixtures.create_instrument()

    def test_statisticks_ok(self):
        Fixtures.change_fiat_balance(self.user1, 500)
        Fixtures.change_fiat_balance(self.user2, 500)
        order1 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user1,
                                       type=models.OrderType.SELL.value,
                                       amount=100, price=1)
        order2 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user2,
                                       type=models.OrderType.BUY.value,
                                       amount=100, price=1)
        Fixtures.change_instrument_balance(self.user1, self.instrument, 100)
        Fixtures.change_instrument_balance(self.bank, self.instrument, 500)
        _ = models.Order._trade_orders(
            order1, order2)
        price = models.Order.get_avg_price(self.instrument)
        bank_balance = models.Order.get_placed_assets_rate(self.instrument)
        liquidity = models.Order.get_liquidity_rate(self.instrument)
        self.assertEqual(price, 1)
        self.assertEqual(bank_balance, 500)
        self.assertEqual(liquidity, 0)
