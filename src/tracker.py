import os
import random
import time

import smtplib
from email.mime.text import MIMEText
from markdown2 import markdown

import sys

from api import CashpassportApi
from banking import BankAccount, Transaction, TransactionList

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

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

        self.__email_from = credentials[4]
        self.__email_password = credentials[5]
        self._mail_server = credentials[6]
        self.__email_to = credentials[7]

        if self._api.login():
            self._bank_account = BankAccount(self._api.get_user_id(), log_function=log_function)
            self._bank_account.load_attributes()
        else:
            self.log("Initial login error")

    def get_api(self):
        return self._api

    def _make_email_msg(self):
        content = ""
        content +=
        content = "# You spent some money!\n"
        content += "\n"
        content += "### Account balance: " + '{:,.2f}'.format(balance) + " EUR\n"
        content += "\n\n"
        content += "# Recent transactions: \n"
        content += "\n"

        for transaction in new_transactions:
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
        msg['From'] = self.__email_from  # some SMTP servers will do this automatically, not all


    def send_info_email(self):

        msg = self._make_email_msg()

        for i in range(3):
            try:
                try:
                    conn = smtplib.SMTP(self._mail_server)
                    conn.set_debuglevel(1)
                    conn.starttls()
                except:
                    conn = smtplib.SMTP(self._mail_server)
                    conn.set_debuglevel(1)

                conn.login(self.__email_from, self.__email_password)
                conn.sendmail(self.__email_from, self.__email_to, msg.as_string())
                conn.quit()
                self.log("-------------")
                self.log("Succesfully sent!")
                return True
            except smtplib.SMTPException as e:
                self.log("Could not send email: " + str(e) + "; " + str(type(e)))

                try:
                    conn.quit()
                except:
                    pass

                if type(e) != smtplib.SMTPServerDisconnected:
                    return False
                self.log("Retrying email")

        self.log("Error with email")
        return False

    def poll(self):
        # Check the account balance to see if it has changed

        self.log("Reading balance")
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

        self.log("Reading transactions")
        recent_transactions = self._api.get_recent_transactions()
        new_transactions = TransactionList()

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
                self.log("New transaction: " + str(transaction))

        if balance != old_balance
            if not self.send_info_email():
                return False
        else:
            self.log("No new activity")
        return True

    def random_sleep(self):
        sleep_time = 1
        #sleep_time = random.randint(3*60*60, 5*60*60)
        self.log("Refreshing in: " + str(sleep_time) + " seconds")
        time.sleep(sleep_time)  # only refresh every 3-5 hours

    def main_loop(self):
        self.log("Main loop started")
        while self.poll():
            self.random_sleep()


def load_credentails():
    credentials = []
    #################
    # Credentials file is lines of the following:
    #
    # user_id
    # password
    # website verification message
    # secuirty answer
    # email to send from
    # password for email
    # smtp mail server
    # email to send to
    #################
    try:
        with open(os.path.join(MAIN_PATH, "credentials/credentials.conf"), "r") as creds_file:
            for credential in creds_file.readlines():
                credentials.append(credential.strip())
    except Exception as e:
        credentials = []
        print("Error in credentials file: " + str(e))

    return credentials

if __name__ == "__main__":
    credentials = load_credentails()

    if credentials:
        tracker = SpendingTracker(credentials)

        if (tracker.get_api().is_logged_in()):
            tracker.main_loop()
            normal_print("Error in main loop, exiting")
