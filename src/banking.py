import os
import hashlib

from datetime import datetime, timedelta
import time

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

def normal_print(message):
    print message

def format_money(value):
    return '{:,.2f}'.format(value)

def format_euros(value):
    '''
    Converts a value string to a readable euros format. EG 1000 to 1,000 EUR
    '''
    return format_money(value) + " EUR"

class Transaction:
    TYPE_PURCHACE = 0
    TYPE_WITHDRAWAL = 1
    TYPE_UNKNOWN = -1

    TYPE_MAP = {0: TYPE_PURCHACE, 1: TYPE_WITHDRAWAL, -1: TYPE_UNKNOWN}

    def __init__(self, time=0, place="None", amount=0.0, transaction_type=TYPE_UNKNOWN, verified=False):
        self.__time = int(time)
        self.__place = place
        self.__amount = amount
        self.__verified = verified
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
                str(self.__amount) +
                str(self.__transaction_type)
            ).encode('utf-8')
        ).hexdigest()

    def get_epoch_time(self):
        return self.__time

    def get_date_time(self):
        return datetime.fromtimestamp(self.__time)

    def get_place(self):
        return self.__place

    def get_amount(self):
        return self.__amount

    def get_data_string(self):
        return ",".join([str(self.get_epoch_time()), self.get_place(), str(self.get_amount()), str(self.get_type()), str(int(self.is_verified()))])

    def __str__(self):
        return "Transaction<" + self.get_data_string() + ">"

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return Transaction(self.get_epoch_time(), self.get_place(), self.get_amount(), self.get_type(), self.is_verified())

    def is_verified(self):
        return self.__verified


class TransactionList(list):
    '''
    Every transaction when stored in a list is stored in this class so that
    the lists can then be analysed for creating data output
    '''

    def sort(self):
        list.sort(self, key=lambda transaction: transaction.get_epoch_time())

    def between(self, start, end):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_epoch_time() >= start and transaction.get_epoch_time() <= end:
                transactions.append(transaction.copy())

        return transactions.copy()

    def at(self, place):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_place() == place:
                transactions.append(transaction.copy())

        return transactions.copy()

    def of_type(self, type):
        transactions = TransactionList()
        for transaction in self:
            if transaction.get_type() == type:
                transactions.append(transaction.copy())

        return transactions.copy()

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

        return self.between(start_timestamp, time.time())

    def this_month(self):
        now = datetime.now()

        start_of_month_date = now.replace(day = 1).date()
        start_timestamp = time.mktime(start_of_month_date.timetuple())

        return self.between(start_timestamp, time.time())

    def this_year(self):
        now = datetime.now()

        start_of_year_date = now.replace(day=1, month=1).date()
        start_timestamp = time.mktime(start_of_year_date.timetuple())

        return self.between(start_timestamp, time.time())

    def append(self, transaction):
        list.append(self, transaction)
        self.sort()

    def copy(self):
        new_list = TransactionList()
        for transaction in self:
            new_list.append(transaction.copy())

        return new_list

class BankAccount:
    def __init__(self, user, balance=0.0, transactions=None, log_function=normal_print):
        def banking_log(message):
            log_function("[BANKING] " + message)

        self.log = banking_log

        if not transactions:
            transactions = TransactionList()
        self.__user = user
        self.__balance = balance
        self.__transactions = transactions
        self.__account_file = os.path.join(MAIN_PATH, "accounts/" + self.__user + "_account.txt")

    def get_account_file_path(self):
        return self.__account_file

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

    def _set_balance(self, balance):
        self.__balance = balance

    def new_balance(self, balance):
        self._set_balance(balance)
        self.save_attributes()

    def _set_transactions(self, transactions):
        self.__transactions = transactions.copy()

    def _add_transaction(self, transaction):
        self.__transactions.append(transaction.copy())

    def new_transaction(self, transaction):
        self._add_transaction(transaction)
        self.save_attributes()

    def has_transaction(self, transaction):
        return self.get_transaction_with_hash(transaction.get_hash()) != None

    def load_attributes(self):
        if os.path.isfile(self.__account_file):
            try:
                with open(self.__account_file, "r") as transactions_file:
                    self._set_transactions(TransactionList())
                    self._set_balance(0)

                    for line in transactions_file.readlines():
                        if line.strip() != "":
                            if "," in line.strip():
                                # Tranactions are saved as time,place,amount in a txt
                                time, place, amount, type, verified = line.strip().split(",")

                                self._add_transaction(
                                    Transaction(
                                        int(time),
                                        place,
                                        float(amount),
                                        int(type),
                                        bool(int(verified))
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
            transactions_file.write(self.get_raw_data())

    def get_raw_data(self):
        data = ""
        for transaction in self.__transactions:
            data += transaction.get_data_string() + "\n"
        data += "\n"
        data += str(self.get_balance()) + "\n"
        return data
