import os
import calendar
import logging
import requests

from banking import Transaction, TransactionList

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(MAIN_PATH, "test_pages")):
    os.mkdir(os.path.join(MAIN_PATH, "test_pages"))

def to_utc_timestamp(date_time):
    return calendar.timegm(date_time.utctimetuple())

class CashpassportApiError(Exception):
    pass

class CashpassportApiConnectionError(Exception):
    pass

class CashpassportApi:
    _GET_BALANCE_PAGE = "/get-balance"
    _GET_TRANSACTIONS_PAGE = "/get-transactions"
    _LOGIN = "/login"
    _LOGOUT = "/logout"

    ERROR_BAD_PASSWORD = 0
    ERROR_BAD_USER_ID = 1
    ERROR_BAD_SECURITY_MESSAGE = 2
    ERROR_BAD_SECURITY_ANSWER = 3

    ERROR_LOGGED_OUT = -200000

    ERROR_LOGIN_IN_PROGRESS = 5
     
    def __init__(self, address="localhost:5000"):
        self._address = address
        self.__logged_in_token = ""

    def login(self, user, password, message, answer, timezone):
        try:
            response = requests.post(self._address + CashpassportApi._LOGIN)
        except Exception:
            raise CashpassportApiConnectionError()
            
        if response.status != 200:
            raise CashpassportApiError()
            
        data = response.json
        

    def is_logged_in(self):
        return self.__logged_in_token

    def logout(self):
        return True

    def get_transactions(self, from_ts=0):
        '''
        Parses the transaction page for all transactions until the given timestamp

        returns empty or not logged if it couldn't connect
        '''
        transactions = TransactionList()

        requests.get("localhost")

        return transactions

    def get_balance(self):
        return False

if __name__ == "__main__":
    pass