from datetime import timedelta
from decimal import Decimal

from django.test import TestCase

from client_user import models

from .utils import Fixtures


class BaseTestCase(TestCase):
    def setUp(self):
        self.user1 = Fixtures.create_user('pes@mail.ru', 0)
        self.user2 = Fixtures.create_user('psina@mail.ru', 0)
        self.instrument = Fixtures.create_instrument()

    def test_trade_two_orders(self):
        Fixtures.change_fiat_balance(self.user1, 500)
        Fixtures.change_fiat_balance(self.user2, 500)
        order1 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user1,
                                       type=models.OrderType.SELL.value,
                                       amount=100,
                                       price=1)
        order2 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user2,
                                       type=models.OrderType.BUY.value,
                                       amount=100,
                                       price=1)
        Fixtures.change_instrument_balance(self.user1, self.instrument, 100)
        order1, order2, first_balance, second_balance, first_fiat_balance, second_fiat_balance = models.Order._trade_orders(
            order1, order2)
        self.assertEqual(order1.status, models.OrderStatus.COMPLETED.value)
        self.assertEqual(order2.status, models.OrderStatus.COMPLETED.value)
        self.assertEqual(first_balance.amount, 0)
        self.assertEqual(second_balance.amount, 100)
        self.assertEqual(first_fiat_balance.amount, 600)
        self.assertEqual(second_fiat_balance.amount, 400)

    def test_trade_two_orders_reverse_order(self):
        Fixtures.change_fiat_balance(self.user1, 500)
        Fixtures.change_fiat_balance(self.user2, 500)
        order1 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user1,
                                       type=models.OrderType.BUY.value,
                                       amount=100,
                                       price=1)
        order2 = Fixtures.create_order(instrument=self.instrument,
                                       user=self.user2,
                                       type=models.OrderType.SELL.value,
                                       amount=100,
                                       price=1)
        Fixtures.change_instrument_balance(self.user2, self.instrument, 100)
        order1, order2, first_balance, second_balance, first_fiat_balance, second_fiat_balance = models.Order._trade_orders(
            order1, order2)
        self.assertEqual(order1.status, models.OrderStatus.COMPLETED.value)
        self.assertEqual(order2.status, models.OrderStatus.COMPLETED.value)
        self.assertEqual(second_balance.amount, 0)
        self.assertEqual(first_balance.amount, 100)
        self.assertEqual(second_fiat_balance.amount, 600)
        self.assertEqual(first_fiat_balance.amount, 400)

    def test_trade_multiple_orders_against_one(self):
        Fixtures.change_instrument_balance(self.user1, self.instrument, 900)
        Fixtures.change_fiat_balance(self.user2, 900)
        sell_order = models.Order(user=self.user1,
                                  instrument=self.instrument,
                                  type=models.OrderType.SELL.value,
                                  total_sum=900,
                                  remaining_sum=900,
                                  price=1,
                                  expires_in=timedelta(days=1).total_seconds())
        buy_orders = [
            Fixtures.create_order(self.user2, self.instrument,
                                  models.OrderType.BUY.value, 300, 1)
            for _ in range(3)
        ]
        sell_order = models.Order.place_order(sell_order)
        first_fiat_balance = models.FiatBalance.objects.get(user=self.user1)
        second_fiat_balance = models.FiatBalance.objects.get(user=self.user2)
        first_instrument_balance = models.InstrumentBalance.objects.get(
            user=self.user1, instrument=self.instrument)
        second_instrument_balance = models.InstrumentBalance.objects.get(
            user=self.user2, instrument=self.instrument)
        for order in buy_orders:
            order.refresh_from_db()
            self.assertEqual(order.status, models.OrderStatus.COMPLETED.value)
            self.assertEqual(order.remaining_sum, 0)
        self.assertEqual(sell_order.status, models.OrderStatus.COMPLETED.value)
        self.assertEqual(first_fiat_balance.amount, 900)
        self.assertEqual(second_fiat_balance.amount, 0)
        self.assertEqual(first_instrument_balance.amount, 0)
        self.assertEqual(second_instrument_balance.amount, 900)

    def test_trade_multiple_orders_not_fully(self):
        Fixtures.change_instrument_balance(self.user1, self.instrument, 900)
        Fixtures.change_fiat_balance(self.user2, 600)
        sell_order = models.Order(user=self.user1,
                                  instrument=self.instrument,
                                  type=models.OrderType.SELL.value,
                                  total_sum=900,
                                  remaining_sum=900,
                                  price=1,
                                  expires_in=timedelta(days=1).total_seconds())
        buy_orders = [
            Fixtures.create_order(self.user2, self.instrument,
                                  models.OrderType.BUY.value, 300, 1)
            for _ in range(2)
        ]
        sell_order = models.Order.place_order(sell_order)
        first_fiat_balance = models.FiatBalance.objects.get(user=self.user1)
        second_fiat_balance = models.FiatBalance.objects.get(user=self.user2)
        first_instrument_balance = models.InstrumentBalance.objects.get(
            user=self.user1, instrument=self.instrument)
        second_instrument_balance = models.InstrumentBalance.objects.get(
            user=self.user2, instrument=self.instrument)
        for order in buy_orders:
            order.refresh_from_db()
            self.assertEqual(order.status, models.OrderStatus.COMPLETED.value)
            self.assertEqual(order.remaining_sum, 0)
        self.assertEqual(sell_order.status, models.OrderStatus.ACTIVE.value)
        self.assertEqual(sell_order.remaining_sum, 300)
        self.assertEqual(first_fiat_balance.amount, 600)
        self.assertEqual(second_fiat_balance.amount, 0)
        self.assertEqual(first_instrument_balance.amount, 300)
        self.assertEqual(second_instrument_balance.amount, 600)

    def test_trade_with_not_enough_instrument_balance(self):
        Fixtures.change_instrument_balance(self.user1, self.instrument, 500)
        Fixtures.change_fiat_balance(self.user2, 600)
        sell_order = Fixtures.create_order(self.user1, self.instrument,
                                           models.OrderType.SELL.value, 600, 1)
        buy_order = Fixtures.create_order(self.user2, self.instrument,
                                          models.OrderType.BUY.value, 600, 1)
        self.assertRaises(ValueError, models.Order._trade_orders, sell_order,
                          buy_order)

    def test_trade_with_not_enough_fiat_balance(self):
        Fixtures.change_instrument_balance(self.user1, self.instrument, 600)
        Fixtures.change_fiat_balance(self.user2, 500)
        sell_order = Fixtures.create_order(self.user1, self.instrument,
                                           models.OrderType.SELL.value, 600, 1)
        buy_order = Fixtures.create_order(self.user2, self.instrument,
                                          models.OrderType.BUY.value, 600, 1)
        self.assertRaises(ValueError, models.Order._trade_orders, sell_order,
                          buy_order)

    def test_actual_price(self):
        Fixtures.change_fiat_balance(self.user2, 100)
        Fixtures.change_instrument_balance(self.user1, self.instrument, 100)
        sell_order = Fixtures.create_order(self.user1, self.instrument,
                                           models.OrderType.SELL.value, 100,
                                           Decimal(str(0.9)))
        buy_order = Fixtures.create_order(self.user2, self.instrument,
                                          models.OrderType.BUY.value, 100, 1)
        order1, order2, first_balance, second_balance, first_fiat_balance, second_fiat_balance = models.Order._trade_orders(
            buy_order, sell_order)
        self.assertEqual(order1.actual_price, Decimal(str(0.9)))
        self.assertEqual(order2.actual_price, Decimal(str(0.9)))
