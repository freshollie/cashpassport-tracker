import logging
import psycopg2
from datetime import timezone
from transactions import TransactionList, Transaction


class Database:
    def __init__(self, user, password, address):
        pass


class Account:
    def __init__(self, db_conn, account_id):
        self.log = logging.getLogger(Account.__name__ + "<%s>" % account_id)
        self.__db_conn = db_conn
        self.__db_cursor = db_conn.cursor()
        self.__account_id = account_id

    def get_balance(self):
        self.__db_cursor.execute("SELECT balance from accounts WHERE id=%s", (self.__account_id, ))
        return self.__db_cursor.fetchone()[0]

    def get_transactions(self):
        self.__db_cursor.execute("SELECT id, timestamp, amount, place, verified, type FROM Transactions WHERE account_id=%s", (self.__account_id, ))

        transactions = TransactionList()

        for row in self.__db_cursor.fetchall():
            transaction_id, ts, amount, place, verified, transaction_type = row
            ts = ts.replace(tzinfo=timezone.utc).timestamp()
            transaction = Transaction(transaction_id,
                                      ts=ts,
                                      amount=amount,
                                      place=place,
                                      verified=verified,
                                      transaction_type=transaction_type)
            transactions.append(transaction)

        return transactions

    def get_transaction_with_hash(self, hash):
        for transaction in self.get_transactions():
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


if __name__ == "__main__":
    conn = psycopg2.connect(host='', dbname='cashpassport', user='postgres', password='accounts')
    account = Account(conn, 1)
    print(account.get_balance())
    print(account.get_transactions())


