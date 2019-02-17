from itertools import count
from datetime import timedelta

from client_user import models


def get_instrument_name_generator(basename='instrument'):
    counter = count()
    while True:
        c = next(counter)
        yield basename + str(c)


class Fixtures:
    instrument_name_generator = get_instrument_name_generator()

    @classmethod
    def create_user(cls, email, initial_balance=0):
        user = models.ClientUser.objects.create_user(email)
        balance = models.FiatBalance.objects.get(user=user)
        balance.amount += initial_balance
        balance.save()
        return user

    @classmethod
    def create_instrument(cls):
        """
        Create instrument and set balances for every user
        :return:
        """
        instrument = models.Instrument.objects.create(name=next(cls.instrument_name_generator))
        users = models.ClientUser.objects.filter()
        for user in users:
            models.InstrumentBalance.objects.create(instrument=instrument, user=user)
        return instrument

    @classmethod
    def change_instrument_balance(cls, user, instrument, value):
        balance = models.InstrumentBalance.objects.get(user=user, instrument=instrument)
        balance.amount += value
        balance.save()
        return balance

    @classmethod
    def change_fiat_balance(cls, user, value):
        balance = models.FiatBalance.objects.get(user=user)
        balance.amount += value
        balance.save()
        return balance

    @classmethod
    def create_order(cls, user, instrument, type, amount, price):
        return models.Order.objects.create(user=user, instrument=instrument, type=type, total_sum=amount, remaining_sum=amount,
                                           price=price, expires_in=timedelta(days=1))
