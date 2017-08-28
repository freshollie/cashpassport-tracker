import os
import random
import subprocess
import time

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename

import sys

import markdown

from api import CashpassportApi, load_credentails
from banking import BankAccount, Transaction, TransactionList, format_euros

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(MAIN_PATH, "css/github.css"), "r") as f:
    MARKDOWN_CSS = str(f.read())

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
        all_transactions = self._bank_account.get_transactions()

        content = ""
        content += "# CashPassport Account Update\n"
        content += "---\n"
        content += "## Account balance - " + format_euros(self._bank_account.get_balance()) + "\n"
        content += "### Spending\n"

        content += "- This week - " + format_euros(all_transactions.this_week().sum()) + "\n"
        content += "- This month - " + format_euros(all_transactions.this_month().sum()) + "\n"
        content += "- This year - " + format_euros(all_transactions.this_year().sum()) + "\n"

        last_20 = list(reversed(self._bank_account.get_transactions()))[:20]

        if last_20:
            content += "### Last 20 Transactions\n"

            content += "|Date|Type|Place|Amount|\n"
            content += "|-|-|-|-|\n"

            for transaction in last_20:
                type_string = "Unknown type"
                if (transaction.get_type() == Transaction.TYPE_PURCHACE):
                    type_string = "Purchase"
                elif transaction.get_type() == Transaction.TYPE_WITHDRAWAL:
                    type_string = "Withdrawal"

                if not transaction.is_verified():
                    type_string += " - Unverified"

                content += "|" + "|".join([
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transaction.get_epoch_time())),
                    type_string,
                    transaction.get_place(),
                    format_euros(abs(transaction.get_amount()))
                    ]
                ) + "|\n"

        content += "\n*Generated by Cashpassport-Tracker - Oliver Bell - github.com/freshollie/cashpassport-tracker.git*\n"

        self.log("Sending email: ")
        self.log("-------------")
        self.log(content)

        msg = MIMEMultipart('alternative')
        msg['To'] = self.__email_to
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = "CashPassport update - Balance: " + format_euros(self._bank_account.get_balance())
        msg['From'] = self.__email_from  # some SMTP servers will do this automatically, not all

        file_path = self._bank_account.get_account_file_path()

        with open(file_path, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name="account.txt"
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(file_path)
            msg.attach(part)

        # render the markdown into HTML
        html_content = markdown.markdown(content, ['extra', 'codehilite'])
        html_content = '<style type="text/css">' + \
                       MARKDOWN_CSS + '</style>' + html_content

        msg.attach(MIMEText(content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        return msg


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
                if not self.DEV: conn.sendmail(self.__email_from, self.__email_to, msg.as_string())
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
                self.log("Retrying email in 10 seconds")
                time.sleep(10)

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
            self._bank_account.new_balance(balance)

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
                transaction_updated = False

                # Even if the hash has not been found, check if a transaction has just been verified
                # With the same amount on the same day, within 20 mins of eachother,
                # and the name of the place has the same first word
                if (transaction.is_verified()):
                    for old_transaction in self._bank_account.get_transactions():
                        time_difference_minutes = ((old_transaction.get_date_time() - transaction.get_date_time())
                                           .total_seconds() / 60)
                        old_start_word = old_transaction.get_place().split("\\")[0].split(" ")[0]

                        if (old_transaction.get_date_time().date() == transaction.get_date_time().date() and
                                    time_difference_minutes < 20 and
                                    old_transaction.get_amount() == transaction.get_amount() and
                                    transaction.get_place().startswith(old_start_word) and
                                    not old_transaction.is_verified()):

                            new_transactions.append(transaction)
                            self._bank_account.update_transaction(old_transaction.get_hash(), transaction)

                            self.log("A Transaction has been verified")
                            self.log("Updated transaction: " + str(old_transaction))
                            self.log("With verified transaction: " + str(transaction))
                            transaction_updated = True
                            break

                if not transaction_updated:
                    new_transactions.append(transaction)
                    self._bank_account.new_transaction(transaction)
                    self.log("New transaction: " + str(transaction))
            else:
                # As this transaction already exists, check if
                old_transaction = self._bank_account.get_transaction_with_hash(transaction.get_hash())
                if old_transaction.is_verified() != transaction.is_verified():
                    new_transactions.append(transaction)
                    self._bank_account.update_transaction(old_transaction.get_hash(), transaction)

                    self.log("A Transaction has been verified")
                    self.log("Updated transaction: " + str(old_transaction))
                    self.log("With verified transaction: " + str(transaction))

        if balance != old_balance or new_transactions:
            if not self.send_info_email():
                return False
        else:
            self.log("No new activity")
        return True

    def get_random_sleep_time(self):
        return random.randint(3*60*60, 5*60*60)

    def random_sleep(self):
        sleep_time = self.get_random_sleep_time()
        self.log("Refreshing in: " + str(sleep_time) + " seconds")
        time.sleep(sleep_time)  # only refresh every 3-5 hours

    def main_loop(self):
        self.log("Main loop started")
        while self.poll:
            self.random_sleep()

if __name__ == "__main__":
    credentials = load_credentails()

    SpendingTracker.DEV = True

    if credentials:
        tracker = SpendingTracker(credentials)

        if (tracker.get_api().is_logged_in()):
            tracker.main_loop()
            normal_print("Error in main loop, exiting")
