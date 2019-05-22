from django.contrib import admin

from . import models

# Register your models here.

admin.site.register(models.ClientUser)
admin.site.register(models.Instrument)
admin.site.register(models.Order)
admin.site.register(models.InstrumentBalance)
admin.site.register(models.Currency)
