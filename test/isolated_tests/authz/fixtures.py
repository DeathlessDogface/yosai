import pytest
import copy
from unittest.mock import create_autospec

from yosai import (
    ModularRealmAuthorizer,
    OrderedSet,
    SimpleAuthorizationInfo,
    SimpleRole,
    WildcardPermission,
)

from .doubles import (
    MockAuthzAccountStoreRealm,
    MockPermission,
)


@pytest.fixture(scope='function')
def authz_realms_collection_ftf(monkeypatch):
    """
    the three realms return True, False, True
    """
    true_mock_realm = MockAuthzAccountStoreRealm()
    monkeypatch.setattr(true_mock_realm, 'has_role', lambda *args: True) 
    monkeypatch.setattr(true_mock_realm, 'is_permitted', lambda *args: True) 

    dumbmock1 = type('DumbMock1', (object,), {})
    dumbmock2 = type('DumbMock2', (object,), {})
    return {MockAuthzAccountStoreRealm(), true_mock_realm,
            MockAuthzAccountStoreRealm(), dumbmock1(), dumbmock2()}

@pytest.fixture(scope='function')
def authz_realms_collection_fff(monkeypatch):
    """
    the three realms return True, False, True
    """
    dumbmock1 = type('DumbMock1', (object,), {})
    dumbmock2 = type('DumbMock2', (object,), {})
    return {MockAuthzAccountStoreRealm(), MockAuthzAccountStoreRealm(),
            MockAuthzAccountStoreRealm(), dumbmock1(), dumbmock2()}

@pytest.fixture(scope='function')
def modular_realm_authorizer_ftf(monkeypatch, authz_realms_collection_ftf):
    a = ModularRealmAuthorizer()
    monkeypatch.setattr(a, '_realms', authz_realms_collection_ftf)
    return a

@pytest.fixture(scope='function')
def modular_realm_authorizer_fff(monkeypatch, authz_realms_collection_fff):
    a = ModularRealmAuthorizer()
    monkeypatch.setattr(a, '_realms', authz_realms_collection_fff)
    return a

@pytest.fixture(scope='function')
def simple_authz_info():
    return SimpleAuthorizationInfo()

@pytest.fixture(scope='function')
def populated_simple_role():
    name = 'SimpleRole123'
    permissions = OrderedSet([MockPermission(False), 
                              MockPermission(False),
                              MockPermission(True)])
    return SimpleRole(name=name, permissions=permissions)

@pytest.fixture(scope='function')
def default_wildcard_permission():
    return WildcardPermission()