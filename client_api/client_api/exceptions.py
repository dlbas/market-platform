from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException


class Http404(APIException):
    status_code = 404


class TotpBadTokenError(APIException):
    status_code = 500
    default_detail = _('Invalid totp_token. Try to disable.')
    default_code = 'bad_totp_token'


class TwoFactorFailed(APIException):
    status_code = 400
    default_detail = _('Invalid two factor code.')
    default_code = 'invalid_two_factor_code'


class EmailNotConfirmed(APIException):
    status_code = 400
    default_detail = _('Email not confirmed.')
    default_code = 'email_not_confirmed'


class EmailTemplateNotFound(APIException):
    status_code = 400
    default_detail = _('Email template not found.')
    default_code = 'email_not_confirmed'


class InvalidExchangeError(APIException):
    status_code = 400
    default_detail = _('Invalid exchange operation.')
    default_code = 'invalid_exchange_operation'


class NotEnoughBalance(APIException):
    status_code = 400
    default_detail = _('Not enough balance.')
    default_code = 'not_enough_balance'


class TwoFactorDisabled(APIException):
    status_code = 400
    default_detail = _('Two factor disabled.')
    default_code = 'two_factor_disabled'


class NoVacantWallets(APIException):
    status_code = 500
    default_detail = _('No vacant wallets.')
    default_code = 'no_vacant_wallets'


class ReachedReassignLimit(APIException):
    status_code = 400
    default_detail = _('Following user reached re-assign limit.')
    default_code = 'reached_reassign_limit'


class TooOftenReassign(APIException):
    status_code = 400
    default_detail = _('Too often reassign request.')
    default_code = 'too_often_reassign'


class PriceAgentError(APIException):
    status_code = 400


class WrongCurrency(APIException):
    status_code = 400
    default_detail = _('Wrong currency chosed.')
    default_code = 'wrong_currency'


class CountryIsBlocked(APIException):
    status_code = 400
    default_detail = _('This country is blocked.')
    default_code = 'country_blocked'


class CountryIsUndefined(APIException):
    status_code = 500
    default_detail = _(
        'This country is undefined. Ask meneger to continue registration.')
    default_code = 'country_undefined'


class CurrenciesPairRateNotFound(APIException):
    status_code = 404
    default_detail = _('Currencies pair rate not found')
    default_code = 'currencies_pair_rate_not_found'


class OperationNotEnabled(APIException):
    status_code = 403
    default_detail = _('Operation is not enabled')
    default_code = 'operation_is_not_enabled'


class OperationSettingsNotFound(APIException):
    status_code = 404
    default_detail = _('Operation settings not found')
    default_code = 'operation_settings_not_found'


class AmountIsOutOfLimits(APIException):
    status_code = 400
    default_detail = _('Amount is out of limits')
    default_code = 'amount_is_out_of_limits'


class KYCMonthLimitExceed(APIException):
    status_code = 405
    default_detail = _('KYC limit exceeded. Manage your KYC level.')
    default_code = 'kyc_limit_exceeded'


class NoRate(APIException):
    status_code = 400
    default_detail = _('Can not get rate. Bad request')
    default_code = 'no_rate'


class OrderIsFailed(APIException):
    status_code = 400
    default_detail = _('Can not make order. Bad request')
    default_code = 'order_is_failed'


class FromCardNotAllowed(APIException):
    status_code = 400
    default_detail = _(
        'Only authenticated users may use exchange from balance.')
    default_code = 'from_card_not_allowed'


class SchemaNotFound(APIException):
    status_code = 404
    default_detail = _('Schema not found')
    default_code = 'schema_not_found'


class SchemaNotValid(APIException):
    status_code = 400
    default_detail = _('Schema not valid.')
    default_code = 'schema_not_valid'


class WithdrawalLimitExceeded(APIException):
    status_code = 400
    default_detail = _(
        'Withdrawal limit exceeded. Please pass account verification')
    default_code = 'withdrawal_limit_exceeded'


class DepositLimitExceeded(APIException):
    status_code = 400
    default_detail = _(
        'Deposit limit exceeded. Please pass account verification')
    default_code = 'deposit_limit_exceeded'


class UserAlreadyExists(APIException):
    status_code = 400
    default_detail = _('User already exists')
    default_code = 'user_already_exists'


class DepositNotCreated(APIException):
    status_code = 500
    default_detail = _('Create deposit error')
    default_code = 'Create deposit error'


class FastExchangeNotCreated(APIException):
    status_code = 500
    default_detail = _('Create fastexchange error')
    default_code = 'Create_fastexchange_error'


class ChangePasswordWrongPassword(APIException):
    status_code = 400
    default_detail = _('Wrong password.')
    default_code = 'wrong_password'


class ChangePasswordInvalidPassword(APIException):
    status_code = 422


class InvalidRequest(APIException):
    status_code = 400
    default_detail = _('Invalid request.')
    default_code = 'invalid_request'


class SaveFailed(APIException):
    status_code = 422
    default_detail = _('Bad request.')
    default_code = 'bad_request'


class InvalidAddress(APIException):
    status_code = 400
    default_detail = _('Invalid address.')
    default_code = 'invalid_address'


class WithdrawalAlreadyProcessing(APIException):
    status_code = 410
    default_detail = _('Withdrawal already processing. Or not yet created.')
    default_code = 'withdrawal_already_processing'


class WrongCommissionCalculation(APIException):
    status_code = 500
    default_detail = _('Wrong commission calculation. Consult with a support.')
    default_code = 'wrong_commission_calculation'


class WrongAmountCalculation(APIException):
    status_code = 500
    default_detail = _('Wrong amount calculation. Consult with a support.')
    default_code = 'wrong_amount_calculation'


class OperationMatrixDoesNotExist(APIException):
    status_code = 500
    default_detail = _('No such operation.')
    default_code = 'wrong_operation'


class InternalError(APIException):
    status_code = 500
    default_detail = _('Internal error')
    default_code = 'internal_error'


class ActivationError(APIException):
    status_code = 400
    default_detail = _('The code is wrong, or user already activated.')
    default_code = 'activation_error'


class UsedKey(APIException):
    status_code = 400
    default_detail = _('The code already was used.')
    default_code = 'used_key'


class ExpiredKey(APIException):
    status_code = 400
    default_detail = _('The code is expired!')
    default_code = 'expired_key'


class TemplateDoesNotExist(APIException):
    status_code = 400
    default_detail = _('Requested template does not exist')
    default_code = 'template_doesnt_exist'


# Exceptions from core to api


class NotEnoughBalanceException(Exception):
    pass


class CountryIsUndefinedException(Exception):
    pass


class CountryIsBlockedException(Exception):
    pass


class KYCLimitExceedExceptions(Exception):
    pass


class TotpBadTokenException(Exception):
    pass


class TwoFactorFailedExceptions(Exception):
    pass
