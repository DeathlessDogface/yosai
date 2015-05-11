import copy
import traceback

from yosai import (
    AuthenticationException,
    AuthenticationStrategyMissingRealmException,
    IncorrectCredentialsException,
    InvalidAuthenticationTokenException,
    InvalidAuthcAttemptRealmsArgumentException,
    MultiRealmAuthenticationException,
)

from . import (
    DefaultCompositeAccount,
    IAuthenticationAttempt,
    IAuthenticationStrategy,
    IAuthenticationToken,
)

class DefaultAuthenticationAttempt(IAuthenticationAttempt, object):
    """
    DG:  this deviates slightly from Shiro's implementation in that it 
         validates the authc_token, justifiying the existence of this class
         as something more than a simple collection
    """
    def __init__(self, authc_token, realms):
        """
        :type authc_token:  AuthenticationToken
        :type realms: a Set of AccountStoreRealm objects
        """
        self.authentication_token = authc_token
        self.realms = realms  # DG:  frozenset is another option

    @property
    def authentication_token(self):
        return self._authentication_token

    @authentication_token.setter
    def authentication_token(self, token):
        if not isinstance(token, IAuthenticationToken):
            raise InvalidAuthenticationTokenException
        self._authentication_token = token

    @property
    def realms(self):
        return self._realms

    @realms.setter
    def realms(self, realms):
        if not isinstance(realms, set):
            raise InvalidAuthcAttemptRealmsArgumentException
        self._realms = realms


class AllRealmsSuccessfulStrategy(IAuthenticationStrategy, object):
    
    def execute(self, authc_attempt):
        token = authc_attempt.authentication_token
        first_account_realm_name = None
        first_account = None
        composite_account = None

        # realm is an AccountStoreRealm:
        try:
            for realm in authc_attempt.realms:
                if (realm.supports(token)):
                    
                    """
                    If the realm raises an exception, the loop will short
                    circuit, propagating the IncorrectCredentialsException 
                    further up the stack.  As an 'all successful' strategy, if
                    there is even a single exception thrown by any of the
                    supported realms, the authentication attempt is
                    unsuccessful.  This particular implementation also favors
                    short circuiting immediately (instead of trying
                    all realms and then aggregating all potential exceptions)
                    because continuing to access additional account stores is
                    likely to incur unnecessary / undesirable I/O for most apps
                    """
                    # an IncorrectCredentialsException halts the loop:
                    account = realm.authenticate_account(token)
                    
                    if (account):
                        if (not first_account):
                            first_account = account
                            first_account_realm_name = realm.name
                        else:                    
                            if (not composite_account):
                                composite_account = DefaultCompositeAccount()
                                composite_account.append_realm_account(
                                    first_account_realm_name, first_account)
                                
                            composite_account.append_realm_account(
                                realm.name, account) 
        except (TypeError):
            raise AuthenticationStrategyMissingRealmException
        if (composite_account):
            return composite_account

        return first_account


class AtLeastOneRealmSuccessfulStrategy(IAuthenticationStrategy, object):

    def execute(self, authc_attempt):
        """
        :rtype:  Account or DefaultCompositeAccount
        """
        authc_token = authc_attempt.authentication_token
        realm_errors = {} 
        first_account = None
        composite_account = None
        try:
            for realm in authc_attempt.realms:
                if (realm.supports(authc_token)):
                    realm_name = realm.name
                    account = None  # required 

                    try:
                        account = realm.authenticate_account(authc_token)
                    # failed authentication raises an exception:
                    except IncorrectCredentialsException as ex:
                        realm_errors[realm_name] = ex
                    
                    if (account is not None):
                        if (not first_account): 
                            first_account = account
                            first_account_realm_name = realm.name
                        else:
                            if (not composite_account):
                                composite_account = DefaultCompositeAccount()
                                composite_account.append_realm_account(
                                    first_account_realm_name, first_account)
                                
                            composite_account.append_realm_account(
                                realm_name, account)
        except (TypeError):
            raise AuthenticationStrategyMissingRealmException

        if (composite_account is not None):
            return composite_account

        if (first_account is not None): 
            return first_account

        if (realm_errors):  # if no successful authentications
            raise MultiRealmAuthenticationException(realm_errors)

        return None  # DG:  not sure whether code can reach this.. 


class FirstRealmSuccessfulStrategy(IAuthenticationStrategy, object):

    """
     The FirstRealmSuccessfulStrategy will iterate over the available realms
     and invoke Realm.authenticate_account(authc_token) on each one. The moment 
     that a realm returns an Account without raising an Exception, that account
     is returned immediately and all subsequent realms ignored entirely
     (iteration 'short circuits').

     If no realms return an Account:
         * If only one exception was thrown by any consulted Realm, that
           exception is thrown.
         * If more than one Realm threw an exception during consultation, those
           exceptions are bundled together as a
           MultiRealmAuthenticationException and that exception is thrown.
         * If no exceptions were thrown, None is returned, indicating to the
           calling Authenticator that no Account was found.
    """
    def execute(self, authc_attempt):
        """
        :type authc_attempt:  AuthenticationAttempt
        :returns:  Account
        """
        authc_token = authc_attempt.authentication_token
        realm_errors = {} 
        account = None
        try:
            for realm in authc_attempt.realms:
                if (realm.supports(authc_token)):
                    try:
                        account = realm.authenticate_account(authc_token)
                    except Exception as ex:
                        realm_errors[realm.name] = ex
                        # current realm failed - try the next one:
                    else:
                        if (account):
                            # successfully acquired an account
                            # -- stop iterating, return immediately:
                            return account
        except (TypeError):
            raise AuthenticationStrategyMissingRealmException

        if (realm_errors):
            if (len(realm_errors) == 1):
                exc = next(iter(realm_errors.values()))
                if (isinstance(exc, AuthenticationException)):
                    raise exc  # DG:  not sure.. TBD
                
                raise AuthenticationException(
                    "Unable to authenticate realm account.", exc)

            #  else more than one throwable encountered:
            else:
                raise MultiRealmAuthenticationException(realm_errors)

        return None 
