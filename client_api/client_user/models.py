from decimal import Decimal
from enumerate import Enum
import uuid

from django.db import models, transaction
from django.utils import timezone
from django.conf import setting
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.shortcuts import get_object_or_404


def generate_referral_code(length):
    d = uuid.uuid4()
    str = d.hex
    return str[:int(length)]

class Currency(models.Model):
    title = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title}'


class Wallet(models.Model):
    address = models.CharField(max_length=150, unique=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    assigned_at_dt = models.DateTimeField(blank=True, null=True)
    is_owned = models.BooleanField(default=False)


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        with transaction.atomic():
            user = self.model(email=self.normalize_email(email), **extra_fields)
            user.set_password(password)
            user.assign_wallet()
            user.referral_code = generate_referral_code(10)

            # kyc = KYC.objects.create()
            # user.kyc = kyc

            user.save()

            ref_code = extra_fields.get('referral_code', False)
            if ref_code:
                user.set_referrer(ref_code)

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
    status = models.CharField(max_length=128, choices=[(tag.name, tag.value) for tag in ClientUserStatus], default=ClientUserStatus.UNVERIFIED.value)
    is_active = models.BooleanField(default=True)
    password_changed_at_dt = models.DateTimeField(default=timezone.now)
    totp_token = models.CharField(max_length=30, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at_dt = models.DateTimeField(null=True, blank=True)
    email_verification_code = models.UUIDField(default=uuid.uuid4)
    is_only_view_allowed = models.BooleanField(default=False)
    # kyc = models.ForeignKey('client_user.KYC', on_delete=models.PROTECT, null=True, blank=True)
    comment = models.CharField(max_length=500, default='', blank=True)
    language = models.CharField(max_length=5, default='en', blank=True)
    country = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    referral_code = models.CharField(blank=True, max_length=10)
    balance = models.DecimalField(null=False, blank=False, decimal_places=8, max_digits=20, default=Decimal(1.00))
    wallet = models.ForeignKey(Wallet, blank=True, null=True, on_delete=models.DO_NOTHING)
    referrer = models.ForeignKey("client_user.ClientUser", blank=True, null=True, on_delete=models.DO_NOTHING)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    @classmethod
    def activate(cls, code):
        user = get_object_or_404(cls, email_verification_code=code)

        if not user.is_email_verified and user.email_verification_code == code:
            user.is_email_verified = True
            user.email_verification_date = timezone.now()
            user.save(update_fields=[
                'is_email_verified',
                'email_verification_date',
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

    # def disable_two_factor(self):
    #     if self.is_two_factor_enabled:
    #         self.is_two_factor_enabled = False
    #         self.save(update_fields=['is_two_factor_enabled'])
    #
    # def enable_two_factor(self):
    #     if not self.is_two_factor_enabled:
    #         self.is_two_factor_enabled = True
    #         self.save(update_fields=['is_two_factor_enabled'])

    def generate_totp_token(self):
        self.totp_token = pyotp.random_base32()
        self.save(update_fields=['totp_token'])

    def assign_wallet(self):
        with transaction.atomic():
            try:
                wallet = Wallet.objects.select_for_update().filter(is_owned=False).first()
            except Exception as e:
                return None

            self.wallet = wallet
            self.save()
            wallet.assign_date = timezone.now()
            wallet.is_owned = True
            wallet.save()

        return wallet.address

    def set_referrer(self, code):
        referrer = ClientUser.objects.filter(referral_code=code).first()
        if not referrer:
            return False
        self.referrer = referrer
        return self.save()

    def add_billing(self, operation, amount, referral=None):
        return Billing(
            user=self,
            wallet=self.wallet,
            operation=operation,
            amount=amount,
            referral=referral
        ).save()

    def check_amount(self, amount):
        if self.balance < amount:
            raise Exception("You have not enough money for this operation")
        return True

    # Комиссия за запрос
    def take_commission(self):
        commission = settings.BILLING['commission']
        self.check_amount(commission)
        self.add_billing(Operations.commission.value, commission)
        self.balance -= Decimal(commission)
        self.save()

    # Награда за реферала
    def add_referral(self, reward, referral):
        self.add_billing(Operations.referral.value, reward, referral)
        self.balance += Decimal(reward)
        self.save()

    def add_reward(self, reward):
        self.add_billing(Operations.reward.value, reward)
        self.balance += Decimal(reward)
        self.save()


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

class Billing(models.Model):
    operation = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in Operations])
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    operation = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in Operations])
    amount = models.DecimalField(decimal_places=8, max_digits=20, default=Decimal(0.00))
    created_at_dt = models.DateTimeField(auto_now_add=True)


class InstrumentStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DELETED = 'deleted'


class Instrument(models.Model):
    name = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in InstrumentStatus])
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)


class OrderType(Enum):
    SELL = 'sell'
    BUY = 'buy'

class OrderStatus(Enum):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    DELETED = 'deleted'

class Order(models.Model):
    type = models.CharField(max_length=15, choices=[(tag, tag.value) for tag in OrderType])
    status = models.CharField(max_length=30, choices=[(tag, tag.value) for tag in OrderStatus])
    instrument_from = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    instrument_to = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    total_sum = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    remaining_sum = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at_dt = models.DateTimeField(auto_now_add=True)
    updated_at_dt = models.DateTimeField(auto_now=True)
    expires_in = models.DurationField()
