import logging

from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


logger = logging.getLogger('django.views')


class JWTWithNoTotpAuthentication(JSONWebTokenAuthentication):
    def authenticate_credentials(self, payload):
        import pdb;pdb.set_trace()
        logger.error(payload)
        user = super().authenticate_credentials(payload)

        orig_iat = int(payload['orig_iat'])
        password_last_changed = int(user.password_changed_at_dt.timestamp())

        if orig_iat < password_last_changed:
            msg = 'Users must re-authenticate after changing password.'
            raise exceptions.AuthenticationFailed(msg)

        return user


class JWTWithTotpAuthentication(JWTWithNoTotpAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)

        if auth_result is not None:
            user, jwt_token = auth_result
        else:
            # it's not a mistake
            # for public APIs
            return None

        # if user.is_two_factor_enabled:
            # two_factor_code = request.data.get('two_factor_code')
            # if not is_two_factor_valid(two_factor_code, user):
            #     raise TwoFactorFailed
        return user, jwt_token
