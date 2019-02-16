from enum import Enum
import uuid
import pyotp

from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from client_api import exceptions


def generate_referral_code(length):
    d = uuid.uuid4()
    str = d.hex
    return str[:int(length)]


class Currency(models.Model):
    title = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title}'


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        with transaction.atomic():
            user = self.model(email=self.normalize_email(email), **extra_fields)
            user.set_password(password)
            user.save()
            # TODO HARDCODE USD
            user.assign_fiat_balance('USD')

            return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password=password, **extra_fields)


class ClientUserStatus(Enum):
    VERIFIED = 'verified'
    UNVERIFIED = 'unverified'


class ClientUser(AbstractBaseUser):
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)
    email = models.EmailField(max_length=40, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=128, choices=[(tag.name, tag.value) for tag in ClientUserStatus],
                              default=ClientUserStatus.UNVERIFIED.value)
    is_active = models.BooleanField(default=True)
    password_changed_at_dt = models.DateTimeField(default=timezone.now)
    totp_token = models.CharField(max_length=30, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at_dt = models.DateTimeField(null=True, blank=True)
    email_verification_code = models.UUIDField(default=uuid.uuid4)
    is_only_view_allowed = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, default='', blank=True)
    language = models.CharField(max_length=5, default='en', blank=True)
    country = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    @classmethod
    def activate(cls, code):
        user = get_object_or_404(cls, email_verification_code=code)

        if not user.is_email_verified and str(user.email_verification_code) == code:
            user.is_email_verified = True
            user.email_verified_at_dt = timezone.now()
            user.save(update_fields=[
                'is_email_verified',
                'email_verified_at_dt',
            ])
        else:
            raise exceptions.ActivationError

    @property
    def is_staff(self):
        return self.is_superuser

    def change_is_active(self, is_active):
        self.is_active = is_active
        self.save(update_fields=['is_active'])

    def has_perm(self, perm, obj=None):
        return self.is_staff and settings.DEBUG

    def has_module_perms(self, app_label):
        return self.is_staff and settings.DEBUG

    def get_two_factor_qr_url(self):
        if not self.totp_token:
            self.generate_totp_token()
        qr_url = pyotp.totp.TOTP(self.totp_token).provisioning_uri(self.email, issuer_name=settings.TWO_FACTOR_ISSUER)
        return qr_url

    def generate_totp_token(self):
        self.totp_token = pyotp.random_base32()
        self.save(update_fields=['totp_token'])

    def assign_fiat_balance(self, currency_name):
        try:
            currency = Currency.objects.get(title=currency_name)
        except ObjectDoesNotExist:
            currency = Currency.objects.create(title=currency_name)
        FiatBalance.objects.create(user=self, currency=currency)

    def assign_instrument_balance(self, instrument_name):
        instrument = Instrument.objects.get(name=instrument_name)
        InstrumentBalance.objects.create(instrument=instrument, user=self)


class ClientUserIp(models.Model):
    user = models.ForeignKey(ClientUser, blank=False, null=False, on_delete=models.CASCADE, related_name='user_ips')
    ip_address = models.GenericIPAddressField(null=False, blank=False)
    user_agent = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)


class Operations(Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    reward = "reward"
    referral = "referral"
    commission = "commission"


class InstrumentBalance(models.Model):
    user = models.ForeignKey(ClientUser, on_delete=models.PROTECT)
    instrument = models.ForeignKey('Instrument', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    def __str__(self):
        return f'{self.amount} {self.instrument}'


class FiatBalance(models.Model):
    user = models.ForeignKey(ClientUser, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    def __str__(self):
        return f'{self.amount} {self.currency}'


class InstrumentStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DELETED = 'deleted'


class Instrument(models.Model):
    name = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in InstrumentStatus],
                              default=InstrumentStatus.ACTIVE)
    # these ones for underlying credit
    credit_created_at_d = models.DateField(null=True)
    credit_expires_at_d = models.DateField(null=True)
    # expected values like 15.575 %
    credit_interest_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class OrderType(Enum):
    SELL = 'sell'
    BUY = 'buy'


class OrderStatus(Enum):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    DELETED = 'deleted'


class Order(models.Model):
    type = models.CharField(max_length=15, choices=[(tag, tag.value) for tag in OrderType])
    status = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in OrderStatus],
                              default=OrderStatus.ACTIVE)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name='instrument')
    total_sum = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    remaining_sum = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)
    expires_in = models.DurationField()
    user = models.ForeignKey(ClientUser, on_delete=models.PROTECT)

    def __str__(self):
        return f'[{self.type}|{self.instrument}] @{self.price} ({self.remaining_sum}/{self.total_sum})'

    @classmethod
    def _trade_orders(cls, first, second):
        """

        :param first:
        :param second:
        :return:
        """
        # TODO Add fee
        with transaction.atomic():
            trade_amount = min(first.remaining_sum, second.remaining_sum)
            first_balance = InstrumentBalance.objects.select_for_update().get(user=first.user,
                                                                              instrument=first.instrument)
            second_balance = InstrumentBalance.objects.select_for_update().get(user=second.user,
                                                                               instrument=first.instrument)
            first_fiat_balance = FiatBalance.objects.select_for_update().get(user=first.user)
            second_fiat_balance = FiatBalance.objects.select_for_update().get(user=second.user)
            if not first_balance:
                raise ValueError(f'Balance for user {first.user} in instrument not found')
            if not second_balance:
                raise ValueError(f'Balance for user {second.user} in instrument not found')
            if first.type == OrderType.BUY and first_fiat_balance.amount < trade_amount * second.price:
                raise ValueError(f'Not enough funds for {first_fiat_balance.user}')
            if first.type == OrderType.SELL and second_fiat_balance.amount < trade_amount * second.price:
                raise ValueError(f'Not enough funds for {second_fiat_balance.user}')
            if first.type == OrderType.BUY and second_balance.amount < trade_amount:
                raise ValueError(f'Not enough instrument balance for {second_balance.user}')
            if first.type == OrderType.SELL and first_balance.amount < trade_amount:
                raise ValueError(f'Not enough instrument balance for {first_balance.user}')
            first.remaining_sum -= trade_amount
            second.remaining_sum -= trade_amount
            if first.type == OrderType.BUY:
                first_balance.amount += trade_amount
                second_balance.amount -= trade_amount
                first_fiat_balance.amount -= trade_amount * second.price
                second_fiat_balance.amount += trade_amount * second.price
            else:
                first_balance.amount -= trade_amount
                second_balance.amount += trade_amount
                first_fiat_balance.amount += trade_amount * second.price
                second_fiat_balance.amount -= trade_amount * second.price
            if first.remaining_sum == 0:
                first.status = OrderStatus.COMPLETED
            if second.remaining_sum == 0:
                second.status = OrderStatus.COMPLETED
            return first, second, first_balance, second_balance, first_fiat_balance, second_fiat_balance

    @classmethod
    def place_order(cls, order):
        """

        :param order:
        :return:
        """
        counter_order_type = OrderType.SELL if order.type == OrderType.BUY else OrderType.BUY
        counter_orders = None
        with transaction.atomic():
            if counter_order_type == OrderType.SELL:
                counter_orders = cls.objects.select_for_update().filter(
                    type=counter_order_type, instrument=order.instrument, price__lte=order.price
                ).order_by('created_at_dt')
            elif counter_order_type == OrderType.BUY:
                counter_orders = cls.objects.select_for_update().filter(
                    type=counter_order_type, instrument=order.instrument, price__gte=order.price
                ).order_by('created_at_dt')
            if not counter_orders:
                # place order into the order book
                order.save()
                return order
            for counter_order in counter_orders:
                order, counter_order, *balances = cls._trade_orders(order, counter_order)
                order.save()
                counter_order.save()
                for balance in balances:
                    balance.save()
                if order.status == OrderStatus.COMPLETED:
                    return order
        return order
