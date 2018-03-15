import os
import hashlib
import json
import logging

from datetime import datetime, timedelta
import time

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))


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

    def __init__(self, id, ts=0, place=None, amount=0.0, transaction_type=TYPE_UNKNOWN, verified=False):
        self.__id = id;
        self.__time = int(ts)
        if not place:
            place = "None"
        self.__place = place
        self.__amount = amount
        self.__verified = verified
        self.__transaction_type = transaction_type

    def value_to_type(type):
        if type not in Transaction.TYPE_MAP:
            return Transaction.TYPE_UNKNOWN
        return Transaction.TYPE_MAP[type]

    def get_id(self):
        return self.__id

    def get_type(self):
        return self.__transaction_type

    def get_hash(self):
        return hashlib.md5(
            (
                str(self.__time) +
                str(self.__amount) +
                str(self.__transaction_type) +
                str(self.__place) +
                str(self.__verified)
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

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {
            "ts": self.get_epoch_time(),
            "loc": self.get_place(),
            "amount": self.get_amount(),
            "type": self.get_type(),
            "verified": self.is_verified()
        }

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
            if start <= transaction.get_epoch_time() <= end:
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

    def as_simple(self):
        json_list = []
        for transaction in self:
            json_list.append(transaction.to_dict())

        return json_list
