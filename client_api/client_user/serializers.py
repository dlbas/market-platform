from django.conf import settings
from rest_framework import serializers
from django.utils.timezone import now
from django.contrib.auth.password_validation import validate_password
from client_user import models
from django.core.exceptions import ValidationError
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from client_api import exceptions, celery as celery_tasks


class ClientUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClientUser
        fields = ('email', 'first_name', 'last_name', 'created_at_dt', 'language', 'id', 'password', 'balance',
                  'country', 'referral_code',)

    def validate_password(self, password):
        validate_password(password)
        return password

    def save(self, request, *args, **kwargs):
        user = models.ClientUser.objects.create_user(**self.validated_data)
        link = settings.API_URL + '/api/user/verify-email/?code=' + str(user.email_verification_code)

        celery_tasks.send_django_emails_task.delay(
            emails=[user.email],
            subject='Подтверди регистрацию, епта',
            body=f'Тыкай: {link}'
        )


class EmailVerificationSerializer(serializers.Serializer):
    code = serializers.UUIDField()

    def activate_user(self):
        models.ClientUser.activate(code=self.validated_data['code'])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
            return value
        except ValidationError as e:
            raise exceptions.InvalidPassword(e)


class JWTWithTotpSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.fields['two_factor_code'] = serializers.CharField(required=False)

    def get_ip_addr(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_addr = x_forwarded_for.split(',')[0]
        else:
            ip_addr = request.META.get('REMOTE_ADDR')
        return ip_addr

    def get_user_agent(self, request):
        return request.META.get('HTTP_USER_AGENT', '')

    def send_mail(self, user, ip, subject, template):
        celery_tasks.send_django_emails_task.delay(
            emails=[user.email],
            subject=subject,
            body=f'Authorized on ip: {ip}',
        )

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except serializers.ValidationError as exc:
            raise exc

        user = data['user']

        request = self.context['request']

        if not user.is_email_verified:
            # TODO: Send email if email is not verified
            # email_template = EmailTemplate.objects.get(template_type=EmailTemplateTypes.registration.value)
            link = settings.URL_CUSTOMER_UI + '/auth/confirm?code=' + str(user.email_verification_code)

            celery_tasks.send_django_emails_task.delay(
                emails=[user.email],
                subject='Registration confirmation.',
                body=f'Auth link: {link}',
            )
            raise exceptions.EmailNotConfirmed

        user_ip_info, is_created = models.ClientUserIp.objects.update_or_create(user=user,
                                                                                ip_address=self.get_ip_addr(request))
        user_ip_info.user_agent = self.get_user_agent(request)
        user_ip_info.save()

        # if user.ip and is_created:
        #     self.send_mail(user, self.get_ip_addr(request),
        #                    'You have been logged in with new IP', EmailTemplateTypes.login_new_ip.value)

        user.ip = self.get_ip_addr(request)
        user.last_login = now()
        user.save()

        # user_logs.write_auth_log(
        #     request=request,
        #     user=user,
        # )
        return data


# class RequestRestorePasswordSerializer(serializers.Serializer):
#     email = serializers.CharField(required=True)

#     def save(self, request, **kwargs):
#         email = self.validated_data['email']
#         ip = user_logs.get_user_ip(request)
#         user_agent = user_logs.get_user_agent(request)
#         token = models.RestorePasswordToken._create(email,
#                                                     user_logs.get_user_ip(request),
#                                                     user_logs.get_cf_country(request),
#                                                     user_logs.get_user_agent(request))

#         user = models.ClientUser.objects.get(email=email)

#         # send email
#         email_template = EmailTemplate.objects.get(template_type=EmailTemplateTypes.restore_password.value)
#         link = settings.URL_CUSTOMER_UI + '/restore-password?code=' + str(token.key)

#         send_email_task.delay(emails=[email],
#                               subject='Restore password.',
#                               html=email_template.get_html(user.language).replace("#marker_link", link).replace("#marker_ip", ip).replace("#marker_user_agent",user_agent))


# class CheckRestorePasswordSerializer(serializers.Serializer):
#     code = serializers.UUIDField()

#     def check(self, request, **kwargs):
#         code = self.validated_data['code']
#         models.RestorePasswordToken.check_is_valid(code)


# class RestorePasswordSerializer(serializers.Serializer):
#     code = serializers.UUIDField()
#     new_password = serializers.CharField(required=True)

#     def validate_new_password(self, value):
#         try:
#             validate_password(value)
#             return value
#         except ValidationError as e:
#             raise exceptions.ChangePasswordInvalidPassword(e)

#     def restore_password(self, request, **kwargs):
#         code = self.validated_data['code']
#         new_password = self.validated_data['new_password']

#         user = models.RestorePasswordToken.update_password(code, new_password,
#                                                     user_logs.get_user_ip(request),
#                                                     user_logs.get_cf_country(request),
#                                                     user_logs.get_user_agent(request))
#         return user


class InstrumentSerializer(serializers.ModelSerializer):
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
    remaining_sum = serializers.FloatField(required=False)
    type = serializers.ChoiceField(choices=[tag.value for tag in models.OrderType], required=False)

    class Meta:
        model = models.Order
        fields = '__all__'

    def create(self, validated_data):
        return models.Order.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.type = validated_data.get('type', instance.type)
        instance.status = validated_data.get('status', instance.status)
        instance.instrument_from = validated_data.get('instrument_from', instance.instrument_from)
        instance.instrument_to = validated_data.get('instrument_to', instance.instrument_to)
        instance.total_sum = validated_data.get('total_sum', instance.total_sum)
        instance.remaining_sum = validated_data.get('remaining_sum', instance.remaining_sum)
        instance.expires_in = validated_data.get('expires_in', instance.expires_in)
