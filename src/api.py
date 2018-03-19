import logging
import requests

from transactions import Transaction, TransactionList


class CashpassportApiError(Exception):
    ERROR_BAD_PASSWORD = 0
    ERROR_BAD_USER_ID = 1
    ERROR_BAD_SECURITY_MESSAGE = 2
    ERROR_BAD_SECURITY_ANSWER = 3

    ERROR_LOGGED_OUT = 9999

    ERROR_LOGIN_IN_PROGRESS = 5

    def __init__(self, message="", code=-1):
        self.code = code
        self.message = message
        Exception.__init__(self, message)


class CashpassportApiConnectionError(CashpassportApiError):
    pass


class CashpassportApi:
    _ROUTE_GET_BALANCE = "/get-balance"
    _ROUTE_GET_TRANSACTION = "/get-transactions"
    _ROUTE_LOGIN = "/login"
    _ROUTE_LOGOUT = "/logout"
     
    def __init__(self, user, password, message, answer, timezone, address="localhost:5000"):
        if "http" not in address:
            address = "http://" + address

        self.log = logging.getLogger(CashpassportApi.__name__ + "<%s>" % user)
        self.__cred_user = user
        self.__cred_pass = password
        self.__cred_message = message
        self.__cred_answer = answer
        self.__cred_zone = timezone
        self.__api_token = None

        self._address = address

    def login(self):
        '''
        Login must be called before any API can be used
        '''
        self.log.debug("Logging in")
        payload = {
            "user": self.__cred_user,
            "pass": self.__cred_pass,
            "message": self.__cred_message,
            "answer": self.__cred_answer,
            "zone": self.__cred_zone
        }
        try:
            response = requests.post(self._address + CashpassportApi._ROUTE_LOGIN, data=payload)
        except Exception as e:
            print(e)
            raise CashpassportApiConnectionError("Unable to connect to cashpassport API")

        try:
            data = response.json()
        except ValueError:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        if "error" in data:
            raise CashpassportApiError(data["error"], data["code"])

        if "success" not in data or "token" not in data:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        self.__api_token = data["token"]

        self.log.debug("Login successful")

    def is_logged_in(self):
        return (self.__api_token != None)

    def logout(self):
        if not self.is_logged_in():
            return

        self.log.debug("Logging out")

        payload = {
            "token": self.__api_token
        }

        try:
            requests.post(self._address + CashpassportApi._ROUTE_LOGOUT, data=payload)
        except Exception as e:
            raise CashpassportApiConnectionError("Unable to connect to cashpassport API")

        self.__api_token = None

        self.log.debug("Logout complete")

    def get_transactions(self, from_ts=0):
        '''
        Ask the api for a all transactions past the given from ts
        '''

        if not self.is_logged_in():
            raise CashpassportApiError("Not logged in", CashpassportApiError.ERROR_LOGGED_OUT)

        self.log.debug("Getting transactions back to %s" % from_ts)

        payload = {
            "from": from_ts,
            "token": self.__api_token
        }

        try:
            response = requests.get(self._address + CashpassportApi._ROUTE_GET_TRANSACTION, params=payload)
        except Exception as e:
            raise CashpassportApiConnectionError("Unable to connect to cashpassport API")

        try:
            data = response.json()
        except ValueError:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        if "error" in data:
            raise CashpassportApiError(data["error"], data["code"])

        if "transactions" not in data:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        transactions = TransactionList()

        for json_transaction in data["transactions"]:
            transaction = Transaction(ts=json_transaction["ts"],
                                      place=json_transaction["place"],
                                      amount=json_transaction["amount"],
                                      transaction_type=json_transaction["type"],
                                      verified=json_transaction["verified"]
                                      )
            transactions.append(transaction)

        self.log.debug("Found %s transactions" % len(transactions))

        return transactions

    def get_balance(self):
        if not self.is_logged_in():
            raise CashpassportApiError("Not logged in", CashpassportApiError.ERROR_LOGGED_OUT)

        self.log.debug("Getting balance")

        payload = {
            "token": self.__api_token
        }

        try:
            response = requests.get(self._address + CashpassportApi._ROUTE_GET_BALANCE, params=payload)
        except Exception as e:
            raise CashpassportApiConnectionError("Unable to connect to cashpassport API")

        try:
            data = response.json()
        except ValueError:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        if "error" in data:
            raise CashpassportApiError(data["error"], data["code"])

        if "balance" not in data:
            raise CashpassportApiConnectionError("Invalid response from cashpassport API")

        self.log.debug("Balance %s" % data["balance"])
        return data["balance"]


if __name__ == "__main__":
    api = CashpassportApi("redacted",
                          "redacted",
                          "redacted",
                          "redacted",
                          "Europe/Brussels")

    try:
        api.login()
    except CashpassportApiError as e:
        if e.code == CashpassportApiError.ERROR_BAD_SECURITY_MESSAGE:
            print("Bad security message")
        else:
            print("Login failed!")

        raise e

    try:
        print(api.get_balance())
    except CashpassportApiError as e:
        raise e

    try:
        print(api.get_transactions())
    except CashpassportApiError as e:
        raise e

    try:
        print(api.logout())
    except CashpassportApiError as e:
        raise e
