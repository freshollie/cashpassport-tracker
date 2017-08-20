import os
import hashlib

from datetime import datetime, timedelta, time

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

def normal_print(message):
    print message

class Transaction:
    TYPE_PURCHACE = 0
    TYPE_WITHDRAWAL = 1
    TYPE_UNKNOWN = -1

    TYPE_MAP = {0: TYPE_PURCHACE, 1: TYPE_WITHDRAWAL, -1: TYPE_UNKNOWN}

    def __init__(self, time=0, place="None", amount=0.0, transaction_type=TYPE_UNKNOWN):
        self.__time = int(time)
        self.__place = place
        self.__amount = amount
        self.__transaction_type = transaction_type

    def value_to_type(type):
        if type not in Transaction.TYPE_MAP:
            return Transaction.TYPE_UNKNOWN
        return Transaction.TYPE_MAP[type]

    def get_type(self):
        return self.__transaction_type

    def get_hash(self):
        return hashlib.md5(
            (
                str(self.__time) +
                str(self.__place) +
                str(self.__amount) +
                str(self.__transaction_type)
            ).encode('utf-8')
        ).hexdigest()

    def get_time(self):
        return self.__time

    def get_place(self):
        return self.__place

    def get_amount(self):
        return self.__amount

    def get_data_string(self):
        return ",".join([str(self.get_time()), self.get_place(), str(self.get_amount()), str(self.get_type())])

    def __str__(self):
        return "Transaction: " + self.get_data_string()

    def __repr__(self):
        return self.__str__()

class TransactionList(list):
    '''
    Every transaction when stored in a list is stored in this class so that
    the lists can then be analysed for creating data output
    '''

    def between(self, start, end):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_time() >= start and transaction.get_time() <= end:
                transactions.append(transaction)

        return transactions

    def at(self, place):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_place() == place:
                transactions.append(transaction)

        return transactions

    def of_type(self, type):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_type() == type:
                transactions.append(transaction)

        return transactions

    def sum(self):
        sum = 0
        for transaction in self:
            sum += transaction.get_amount()

        # The amounts are usually negative as its money going out
        # So we make it the opposite
        return sum * - 1

    def this_week(self):
        now = datetime.now()

        start_of_week_date = (now - timedelta(days=now.weekday())).date()
        start_timestamp = time.mktime(start_of_week_date.timetuple())

        return self.between(start_timestamp, now)

    def this_month(self):
        now = datetime.now()

        start_of_month_date = now.replace(day = 1).date()
        start_timestamp = time.mktime(start_of_month_date.timetuple())

        return self.between(start_timestamp, now)

    def this_year(self):
        now = datetime.now()

        start_of_year_date = now.replace(day=1, month=1).date()
        start_timestamp = time.mktime(start_of_year_date.timetuple())

        return self.between(start_timestamp, now)


class BankAccount:
        def __init__(self, user, balance=0.0, transactions=None, log_function=normal_print):
            self.log = log_function
            if not transactions:
                transactions = TransactionList()
            self.__user = user
            self.__balance = balance
            self.__transactions = transactions
            self.__account_file = os.path.join(MAIN_PATH, "accounts/" + self.__user + "_account.txt")

        def get_balance(self):
            return self.__balance

        def get_transactions(self):
            return self.__transactions

        def set_balance(self, balance):
            self.__balance = balance

        def set_transactions(self, transaction):
            self.__transactions = transaction

        def _add_transaction(self, transaction):
            self.__transactions.append(transaction)

        def new_transaction(self, transaction):
            self._add_transaction(transaction)
            self.save_attributes()

        def has_transaction(self, transaction):
            for old_transaction in self.__transactions:
                if old_transaction.get_hash() == transaction.get_hash():
                    return True
            return False

        def load_attributes(self):
            if os.path.isfile(self.__account_file):
                try:
                    with open(self.__account_file, "r") as transactions_file:
                        self.set_transactions(TransactionList())
                        self.set_balance(0)

                        for line in transactions_file.readlines():
                            if line.strip() != "":
                                if "," in line.strip():
                                    # Tranactions are saved as time,place,amount in a txt
                                    time, place, amount, type = line.strip().split(",")

                                    self._add_transaction(
                                        Transaction(
                                            int(time),
                                            place,
                                            float(amount),
                                            int(type)
                                        )
                                    )
                                else:
                                    # Line is the balance line
                                    self.__balance = float(line.strip())

                except Exception as e:
                    os.remove(self.__account_file)
                    self.log("Failed to load account: " + e)

        def save_attributes(self):
            if not os.path.isdir(os.path.join(MAIN_PATH, "accounts")):
                os.mkdir(os.path.join(MAIN_PATH, "accounts"))

            with open(self.__account_file, "w") as transactions_file:
                for transaction in self.__transactions:
                    transactions_file.write(transaction.get_data_string() + "\n")
                transactions_file.write("\n")
                transactions_file.write(str(self.get_balance()) + "\n")