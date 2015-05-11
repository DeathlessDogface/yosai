from abc import ABCMeta, abstractmethod


class IAccountId(metaclass=ABCMeta):

    @abstractmethod
    def __repr__(self):
        pass


class IAccount(metaclass=ABCMeta):

    @property 
    @abstractmethod
    def id(self):  # DG:  not happy with this naming convention.. 
        pass

    @property 
    @abstractmethod
    def credentials(self):
        pass

    @property 
    @abstractmethod
    def attributes(self):
        pass


class IAccountStore(metaclass=ABCMeta):

    @abstractmethod
    def get_account(self, authc_token=None, account_id=None):
        pass
