import random
import time

import smtplib
from email.mime.text import MIMEText

from api import CashpassportApi
from banking import BankAccount, Transaction

def normal_print(message):
    print message

class SpendingTracker:
    DEV = False

    def __init__(self, credentials, log_function=normal_print):
        self.log = log_function

        self._api = CashpassportApi(
            credentials[0],
            credentials[1],
            credentials[2],
            credentials[3],
            dev = SpendingTracker.DEV,
            log_function=log_function
        )

        self.__email = credentials[4]
        self.__email_password = credentials[5]
        self._mail_server = credentials[6]

        if self._api.login():
            self._bank_account = BankAccount(self._api.get_user_id(), log_function=log_function)
            self._bank_account.load_attributes()
        else:
            self.log("Initial login error")

    def get_api(self):
        return self._api

    def send_transaction_email(self, transactions, balance):
        content = "You spent some money!\n"
        content += "\n"
        content += "Account balance: " + '{:,.2f}'.format(balance) + " EUR\n"
        content += "\n\n"
        content += "Recent transactions: \n"
        content += "\n"

        for transaction in transactions:
            type_string = "Unknown type"
            if (transaction.get_type() == Transaction.TYPE_PURCHACE):
                type_string = "Purchase"
            elif transaction.get_type() == Transaction.TYPE_WITHDRAWAL:
                type_string = "Withdrawal"

            content += "    " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transaction.get_time()))
            content += ": " + type_string + " @ " + transaction.get_place() + " - "
            content += '{:,.2f}'.format(abs(transaction.get_amount())) + " EUR\n\n"

        self.log("Sending email: ")
        self.log("-------------")
        self.log(content)

        msg = MIMEText(content, 'plain')
        msg['Subject'] = "CashPassport update - Balance : " + '{:,.2f}'.format(balance) + " EUR"
        msg['From'] = self.__email  # some SMTP servers will do this automatically, not all

        try:
            conn = smtplib.SMTP(self._mail_server)
            conn.login(self.__email, self.__email_password)
            conn.sendmail(self.__email, self.__email, msg.as_string())
            conn.quit()
            self.log("-------------")
            self.log("Succesfully sent!")
            return True
        except smtplib.SMTPException as e:
            self.log("Could not send email: " + e)
            conn.quit()
            return False

    def poll(self):
        # Check the account balance to see if it has changed
        old_balance = self._bank_account.get_balance()
        balance = self._api.get_balance()

        if balance == CashpassportApi.ERROR_LOGGED_OUT and not self._api.is_logged_in():
            if self._api.login():
                balance = self._api.get_balance()
                if balance == CashpassportApi.ERROR_LOGGED_OUT and not self._api.is_logged_in():
                    self.log("Error getting balance")
                    return False
            else:
                self.log("Login error")
                return False

        if balance != old_balance:
            self.log("New balance: " + str(balance))
            self._bank_account.set_balance(balance)

        recent_transactions = self._api.get_recent_transactions()
        new_transactions = []

        if recent_transactions == CashpassportApi.ERROR_LOGGED_OUT:
            if self._api.login():
                recent_transactions = self._api.get_recent_transactions()
                if recent_transactions == CashpassportApi.ERROR_LOGGED_OUT:
                    self.log("Error getting recent transactions")
                    return
            else:
                self.log("Login error")
                return False

        for transaction in recent_transactions:
            if not self._bank_account.has_transaction(transaction):
                new_transactions.append(transaction)
                self._bank_account.new_transaction(transaction)

        if new_transactions:
            for transaction in new_transactions:
                self.log("New transaction: " + str(transaction));

            if not self.send_transaction_email(new_transactions, balance):
                return False
        return True

    def random_sleep(self):
        time.sleep(random.randint(30, 60))  # only refresh every 30-60 seconds

    def main_loop(self):
        self.log("Main loop started")
        while self.poll():
            self.random_sleep()


if __name__ == "__main__":
    credentials = []
    #################
    # Config file is lines of the following:
    #
    # user_id
    # password
    # website verification message
    # secuirty answer
    # email to send from and to
    # password for email
    # smtp mail server
    #################
    with open("credentials.conf", "r") as creds_file:
        for credential in creds_file.readlines():
            credentials.append(credential.strip())

    tracker = SpendingTracker(credentials)

    if (tracker.get_api().is_logged_in()):
        tracker.main_loop()
        normal_print("Error in main loop, exiting")
