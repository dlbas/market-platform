# Generated by Django 2.1.5 on 2019-01-21 16:18

import client_user.models
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', models.CharField(choices=[(client_user.models.Operations('deposit'), 'deposit'), (client_user.models.Operations('withdrawal'), 'withdrawal'), (client_user.models.Operations('reward'), 'reward'), (client_user.models.Operations('referral'), 'referral'), (client_user.models.Operations('commission'), 'commission')], max_length=30)),
                ('amount', models.DecimalField(decimal_places=8, default=Decimal('0'), max_digits=20)),
                ('created_at_dt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ClientUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('created_at_dt', models.DateTimeField(auto_now_add=True)),
                ('updated_at_dt', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=40, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=30)),
                ('last_name', models.CharField(blank=True, max_length=30)),
                ('status', models.CharField(choices=[('VERIFIED', 'verified'), ('UNVERIFIED', 'unverified')], default='unverified', max_length=128)),
                ('is_active', models.BooleanField(default=True)),
                ('password_changed_at_dt', models.DateTimeField(default=django.utils.timezone.now)),
                ('totp_token', models.CharField(blank=True, max_length=30)),
                ('is_email_verified', models.BooleanField(default=False)),
                ('email_verified_at_dt', models.DateTimeField(blank=True, null=True)),
                ('email_verification_code', models.UUIDField(default=uuid.uuid4)),
                ('is_only_view_allowed', models.BooleanField(default=False)),
                ('comment', models.CharField(blank=True, default='', max_length=500)),
                ('language', models.CharField(blank=True, default='en', max_length=5)),
                ('country', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, default='', max_length=20)),
                ('is_superuser', models.BooleanField(default=False)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('referral_code', models.CharField(blank=True, max_length=10)),
                ('balance', models.DecimalField(decimal_places=8, default=Decimal('1'), max_digits=20)),
                ('referrer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='client_user.ClientUser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ClientUserIp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=True)),
                ('created_at_dt', models.DateTimeField(auto_now_add=True)),
                ('updated_at_dt', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_ips', to='client_user.ClientUser')),
            ],
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[(client_user.models.InstrumentStatus('active'), 'active'), (client_user.models.InstrumentStatus('inactive'), 'inactive'), (client_user.models.InstrumentStatus('deleted'), 'deleted')], max_length=30)),
                ('created_at_dt', models.DateTimeField(auto_now_add=True)),
                ('updated_at_dt', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[(client_user.models.OrderType('sell'), 'sell'), (client_user.models.OrderType('buy'), 'buy')], max_length=15)),
                ('status', models.CharField(choices=[(client_user.models.OrderStatus('active'), 'active'), (client_user.models.OrderStatus('completed'), 'completed'), (client_user.models.OrderStatus('deleted'), 'deleted')], max_length=30)),
                ('total_sum', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('remaining_sum', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('created_at_dt', models.DateTimeField(auto_now_add=True)),
                ('updated_at_dt', models.DateTimeField(auto_now=True)),
                ('expires_in', models.DurationField()),
                ('instrument_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instrument_from', to='client_user.Instrument')),
                ('instrument_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instrument_to', to='client_user.Instrument')),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=150, unique=True)),
                ('assigned_at_dt', models.DateTimeField(blank=True, null=True)),
                ('is_owned', models.BooleanField(default=False)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_user.Currency')),
            ],
        ),
        migrations.AddField(
            model_name='clientuser',
            name='wallet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='client_user.Wallet'),
        ),
        migrations.AddField(
            model_name='billing',
            name='wallet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_user.Wallet'),
        ),
    ]
