import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models, transaction
from rest_framework.authtoken.models import Token

logger = logging.getLogger('admin models')


class AdminUserManager(BaseUserManager):
    def create_user(self, email, password, is_admin=False):
        logger.info('Creating user')
        user = self.model(email=email)
        user.set_password(password)
        user.is_admin = is_admin
        try:
            with transaction.atomic():
                user.save(using=self._db)
        except Exception as e:
            logger.error('Error creating user')
            logger.error(e)
            return
        return user

    def create_superuser(self, email, password):
        self.create_user(email, password, is_admin=True)


class AdminUser(AbstractBaseUser):
    """Email is authenticating admin user as well as regular one
    """
    email = models.EmailField(max_length=30, unique=True)
    # TODO no need for now
    # secret_key = models.CharField(max_length=32, null=True, blank=True)
    register_date = models.DateTimeField(auto_now=True)
    last_login = models.DateField(auto_now=False,
                                  auto_now_add=False,
                                  null=True,
                                  blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    objects = AdminUserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.get_username()

    def get_short_name(self):
        return self.get_username()

    def __str__(self):  # __unicode__ on Python 2
        return self.get_username()

    def __unicode__(self):
        return self.get_username()

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
