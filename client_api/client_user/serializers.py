from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from client_api import celery as celery_tasks
from client_user import models


class ClientUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClientUser
        fields = ('email', 'first_name', 'last_name', 'created_at_dt',
                  'language', 'id', 'password', 'country')

    def validate_password(self, password):
        validate_password(password)
        return password

    def save(self, request, *args, **kwargs):
        user = models.ClientUser.objects.create_user(**self.validated_data)
        link = settings.API_URL + '/api/user/verify-email/?code=' + str(
            user.email_verification_code)

        celery_tasks.send_django_emails_task.delay(
            emails=[user.email],
            subject='Confirm your registration',
            body=f'Click: {link}')


class InstrumentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=50, required=True)
    status = serializers.CharField(max_length=30, read_only=True)
    # these ones for underlying credit
    credit_created_at_d = serializers.DateTimeField(required=False)
    credit_expires_at_d = serializers.DateTimeField(required=False)
    # expected values like 15.575 %
    credit_interest_percentage = serializers.DecimalField(required=False,
                                                          max_digits=5,
                                                          decimal_places=3)
    created_at_dt = serializers.DateTimeField(read_only=True)
    updated_at_dt = serializers.DateTimeField(read_only=True)

    class Meta:
        model = models.Instrument
        fields = '__all__'

    def create(self, validated_data):
        return models.Instrument.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.status = validated_data.get('status', instance.status)
        return instance


class OrderSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=[tag.value for tag in models.OrderType])
    status = serializers.ChoiceField(
        choices=[tag.value for tag in models.OrderStatus], read_only=True)
    instrument = InstrumentSerializer(read_only=True)
    instrument_id = serializers.IntegerField(write_only=True)
    user = serializers.ReadOnlyField(source='user.id')
    remaining_sum = serializers.DecimalField(max_digits=20,
                                             decimal_places=8,
                                             read_only=True)
    total_sum = serializers.DecimalField(max_digits=20,
                                         decimal_places=8,
                                         write_only=True)
    actual_price = serializers.DecimalField(max_digits=20,
                                            decimal_places=8,
                                            read_only=True)

    class Meta:
        model = models.Order
        fields = [
            'remaining_sum', 'type', 'status', 'expires_in', 'created_at_dt',
            'updated_at_dt', 'total_sum', 'instrument_id', 'instrument',
            'user', 'price', 'actual_price'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        if validated_data['type'] == models.OrderType.BUY.value:
            balance = models.FiatBalance.objects.get(
                user=user, currency__title='USD')  # TODO HARDCODE USD
            if balance.amount < validated_data['total_sum'] * validated_data[
                    'price']:
                raise serializers.ValidationError('Not enough fiat balance')
        elif validated_data['type'] == models.OrderType.SELL.value:
            balance = models.InstrumentBalance.objects.get(
                user=user, instrument=validated_data['instrument_id'])
            if balance.amount < validated_data['total_sum']:
                raise serializers.ValidationError(
                    'Not enough instrument balance')
        order = models.Order(user=user, **validated_data)
        order.remaining_sum = order.total_sum
        return models.Order.place_order(order)

    def update(self, instance, validated_data):
        instance.type = validated_data.get('type', instance.type)
        instance.status = validated_data.get('status', instance.status)
        instance.instrument_from = validated_data.get('instrument_from',
                                                      instance.instrument_from)
        instance.instrument_to = validated_data.get('instrument_to',
                                                    instance.instrument_to)
        instance.total_sum = validated_data.get('total_sum',
                                                instance.total_sum)
        instance.remaining_sum = validated_data.get('remaining_sum',
                                                    instance.remaining_sum)
        instance.expires_in = validated_data.get('expires_in',
                                                 instance.expires_in)
        return instance


class FiatBalanceSerializer(serializers.ModelSerializer):
    currency = serializers.StringRelatedField(read_only=True)
    user = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = models.FiatBalance
        fields = '__all__'
        lookup_field = 'id'

    def update(self, instance, validated_data):
        instance.amount = validated_data.get('amount', 0)
        instance.save()
        return instance


class InstrumentBalanceSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    instrument = serializers.ReadOnlyField(source='instrument.id')

    class Meta:
        model = models.InstrumentBalance
        fields = '__all__'
        lookup_field = 'id'

    def update(self, instance, validated_data):
        instance.amount = validated_data.get('amount', 0)
        instance.save()
        return instance


class OrderPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderPriceHistory
        fields = ('price', )


class LiquidityRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LiquidityHistory
        fields = ('value', )


class PlacementRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlacedAssetsHistory
        fields = ('value', )
