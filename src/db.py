import logging
from transactions import TransactionList, Transaction

class Credentials:
    def __init__(self, db_client):
        pass

class UserAccount:
    def __init__(self, user, db_client):
        self.log = logging.getLogger(UserAccount.__name__ + "<%s>" % user)
        self.__db =
        self.__user = user

    def get_balance(self):
        return self.__balance

    def get_transactions(self):
        return self.__transactions.copy()

    def get_transaction_with_hash(self, hash):
        for transaction in self.__transactions:
            if transaction.get_hash() == hash:
                return transaction.copy()
        return None

    # updates the transaction with the given has with a new transaction
    def update_transaction(self, transaction_hash, transaction):
        for i in range(len(self.__transactions)):
            if self.__transactions[i].get_hash() == transaction_hash:
                del self.__transactions[i]
                break

        self.new_transaction(transaction)

    def remove_transaction(self, transaction):
        for i in range(len(self.__transactions)):
            if self.__transactions[i].get_hash() == transaction.get_hash():
                del self.__transactions[i]
                return

    def _set_balance(self, balance):
        self.__balance = balance

    def new_balance(self, balance):
        self._set_balance(balance)

    def _set_transactions(self, transactions):
        self.__transactions = transactions.copy()

    def _add_transaction(self, transaction):
        self.__transactions.append(transaction.copy())

    def new_transaction(self, transaction):
        self._add_transaction(transaction)

    def has_transaction(self, transaction):
        return self.get_transaction_with_hash(transaction.get_hash()) != None
