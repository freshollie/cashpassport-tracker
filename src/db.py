import logging
import psycopg2
from datetime import timezone, datetime
from transactions import TransactionList, Transaction


class CashpassportDB:
    DB_NAME = "cashpassport"

    def __init__(self, user, password, address):
        self.log = logging.getLogger(CashpassportDB.__name__)
        self.__db_address = address
        self.__db_name = CashpassportDB.DB_NAME
        self.__db_user = user
        self.__db_pass = password
        
        self.log.info("Logging into %s. username: %s password: %s", (address, user, password))
        self.__conn = self.__make_conn()
        self.__cursor = self.__conn.cursor()

    def __make_conn(self):
        return psycopg2.connect(host=self.__db_address,
                                dbname=CashpassportDB.DB_NAME,
                                user=self.__db_user,
                                password=self.__db_pass)

    def get_account(self, account_id):
        return Account(self.__make_conn(), account_id)

    def get_tracked_account_ids(self):
        self.__cursor.execute("SELECT id FROM accounts WHERE tracked=true")

        account_ids = []
        for row in self.__cursor.fetchmany():
            account_ids.append(row[0])

        return account_ids

    def get_api_credentials(self, account_id):
        self.__cursor.execute("SELECT username, password, message, answer, timezone FROM accounts WHERE id=%s", (account_id, ))

        row = self.__cursor.fetchone()

        if not row:
            return None

        return {"user": row[0], "pass": row[1], "message": row[2], "answer": row[3], "timezone": row[4]}


class Account:
    def __init__(self, conn, account_id):
        self.log = logging.getLogger(Account.__name__ + "<%s>" % account_id)
        self.__db_conn = conn
        self.__db_cursor = conn.cursor()
        self.__account_id = account_id

    def get_email(self):
        self.__db_cursor.execute("SELECT users.email FROM users, accounts WHERE users.id=accounts.user_id AND accounts.id=%s",
                                 (self.__account_id, ))
        row = self.__db_cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]

    def get_balance(self):
        self.__db_cursor.execute("SELECT balance from accounts WHERE id=%s", (self.__account_id, ))
        return self.__db_cursor.fetchone()[0]

    def set_balance(self, balance):
        self.__db_cursor.execute("UPDATE accounts SET balance=%s WHERE id=%s", (balance, self.__account_id))
        self.__db_conn.commit()

    def get_transactions(self):
        self.__db_cursor.execute("SELECT "
                                 "ts, "
                                 "amount, "
                                 "place, "
                                 "verified, "
                                 "type "
                                 "FROM account_transactions "
                                 "WHERE account_id=%s", (self.__account_id, ))

        transactions = TransactionList()

        for row in self.__db_cursor.fetchall():
            ts, amount, place, verified, transaction_type = row
            ts = ts.replace(tzinfo=timezone.utc).timestamp()
            transaction = Transaction(ts=ts,
                                      amount=amount,
                                      place=place,
                                      verified=verified,
                                      transaction_type=transaction_type)
            transactions.append(transaction)

        return transactions

    def remove_transaction(self, transaction):
        self.__db_cursor.execute("DELETE FROM account_transactions WHERE account_id=%s and hash=%s",
                                 (self.__account_id, transaction.get_hash()))
        self.__db_conn.commit()

    def update_balance(self, balance):
        self.__db_cursor.execute("UPDATE accounts SET balance=%s WHERE id=%s",
                                 (balance, self.__account_id))
        self.__db_conn.commit()

    def new_transaction(self, transaction):
        self.__db_cursor.execute("INSERT INTO account_transactions "
                                 "(ts, place, amount, verified, type, hash, account_id)"
                                 "VALUES"
                                 "(%s, %s, %s, %s, %s, %s, %s)",
                                 (datetime.utcfromtimestamp(transaction.get_epoch_time()),
                                  transaction.get_place(),
                                  transaction.get_amount(),
                                  transaction.is_verified(),
                                  transaction.get_type(),
                                  transaction.get_hash(),
                                  self.__account_id))
        self.__db_conn.commit()

    def has_transaction(self, transaction):
        self.__db_cursor.execute("SELECT hash FROM account_transactions "
                                 "WHERE hash=%s and account_id=%s",
                                 (transaction.get_hash(), self.__account_id))

        return self.__db_cursor.fetchone() != None

    def close_conn(self):
        self.__db_conn.close()


if __name__ == "__main__":
    account = Account(conn, 1)

    lel = Transaction(amount=100)
    account.new_transaction(Transaction(amount=4343))
    print(lel)
    account.new_transaction(lel)
    print(account.get_transactions())
    test = account.get_transactions()[0]
    print(test)
    account.remove_transaction(test)
    test = account.get_transactions()[0]
    print(account.has_transaction(test))
    account.remove_transaction(test)




