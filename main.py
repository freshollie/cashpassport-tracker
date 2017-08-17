import random
import locale
import mechanicalsoup
import sys
import time
import os
import hashlib
from bs4 import BeautifulSoup
import dateutil.parser
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

class Transaction:
    TYPE_PURCHACE = 0
    TYPE_WITHDRAWAL = 1
    TYPE_UNKNOWN = -1

    TYPE_MAP = {0: TYPE_PURCHACE, 1: TYPE_WITHDRAWAL, -1: TYPE_UNKNOWN}

    def __init__(self, time=0, place="None", amount=0, transaction_type=TYPE_UNKNOWN):
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

class BankAccount:
    def __init__(self, user, balance = 0.0, transactions = []):
        self.__user = user
        self.__balance = balance
        self.__transactions = transactions
        self.__user_file = self.__user + "_account.txt"

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
        if (os.path.isfile(self.__user_file)):
            try:
                with open(self.__user_file, "r") as transactions_file:
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
                os.remove(self.__user_file)
                print(e)

    def save_attributes(self):
        with open(self.__user_file, "w") as transactions_file:
            for transaction in self.__transactions:
                transactions_file.write(transaction.get_data_string() + "\n")
            transactions_file.write("\n")
            transactions_file.write(str(self.get_balance()) + "\n")

class Api:
    LOGIN_PAGE = "https://cardholder.mastercardworldwide.com/travelex/cardholder/public/app/registeredCardholderLogin"
    MAIN_PAGE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/cardHolderHome.view"
    VALIDATE_LOGIN_PAGE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/start/extAuth/app/registeredCardHolderPCFCheck"
    SECURITY_ANSWER_PAGE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/start/app/registeredCardHolderLoginSecurityQandA"

    BALANCE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/cardInfo.view?param=&dojo.preventCache="
    TRANSACTIONS_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/currentActivity.view?param=&theme=plain&navId=6&dojo.preventCache="

    LOGIN_FORM_ID = "#registercardholderLoginUseridForm"
    PASSWORD_FORM_ID = "#registercardholderLoginPasswordVerifyForm"
    SECURITY_FORM_ID = "#challengeForm"

    ERROR_BAD_PASSWORD = 0;
    ERROR_BAD_USER_ID = 1;
    ERROR_BAD_SECURITY_MESSAGE = 2;
    ERROR_BAD_SECURITY_ANSWER = 3;

    ERROR_LOGGED_OUT = 4;

    def __init__(self, user_id, password, validation_message, security_answer):
        self.__user_id = user_id
        self.__password = password
        self.__validation_message = validation_message
        self.__security_answer = security_answer
        self._logged_in = False;

    def get_user_id(self):
        return self.__user_id

    def _create_csrfToken_input(self, page):
        '''
        Direct port from the pages javascript

        Inserts the csrf token to the form for submitting
        '''
        token = self._get_cstfToken_from_page(page)

        input = page.new_tag("input")
        input['type'] = 'hidden'
        input['name'] = 'csrfToken'
        input['id'] = 'csrfToken'
        input['value'] = token
        input['defaultValue'] = token
        input['readonly'] = "readonly"

        return input

    def _get_cstfToken_from_page(self, page):
        '''
        Returns the cstf token from the page
        '''
        return page.text.split('var sessionSynchronizationToken = "')[1].split('"')[0]

    def login(self):

        if SpendingTracker.DEV:
            self._logged_in = True
            return self._logged_in

        # Create a new session
        self.browser = mechanicalsoup.StatefulBrowser(
            soup_config={'features': 'lxml'}
        )

        print("Logging in")

        # First present out login id
        self.browser.open(Api.MAIN_PAGE_URL)
        self.browser.select_form(Api.LOGIN_FORM_ID)
        self.browser.get_current_form().form.append(
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )
        self.browser["userIdInput"] = self.__user_id # input username

        print("Submitting username")
        self.browser.submit_selected()

        # Verify it has the correct security message
        page = self.browser.get_current_page()
        print("Security message loaded = " + page.find("div", class_="security_phrase_value").text)

        if page.find("div", class_="security_phrase_value").text != self.__validation_message:
            sys.exit("Bad site, wrong security message")
        else:
            print("Page verified")

        # Verified page so typing password
        self.browser.select_form(Api.PASSWORD_FORM_ID)
        self.browser["password"] = self.__password # Input the password
        self.browser.get_current_form().form["action"] = "/pkmslogin.form"
        self.browser.get_current_form().form.append(
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )
        # self.browser["action"] = "/pkmslogin.form"
        print("Submitting password")
        self.browser.submit_selected()

        # Manually open the urls to verify login
        self.browser.open(Api.VALIDATE_LOGIN_PAGE_URL)

        # Submit the security answer
        self.browser.select_form(Api.SECURITY_FORM_ID)
        self.browser["securityAnswer"] = self.__security_answer # Input the answer

        self.browser.get_current_form().form.insert(
            0,
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )

        input = self.browser.get_current_form().form.find_all("input", {"name": "autoLogonOption"})[0]
        input["checked"] = "false"
        input["value"] = "false"

        print("Submitting security answer")
        self.browser.submit_selected()
        self.browser.open(Api.MAIN_PAGE_URL)

        if self.browser.get_current_page().find("a", href="/travelex/cardholder/chProfile.view"):
            print("Login successful")
            self._logged_in = True
        else:
            self._logged_in = False
            print("Login unsuccessful")
            print(self.browser.get_current_page().find_all("a"))

        return self._logged_in

    def is_logged_in(self):
        return self._logged_in

    def _get_authorised_page(self, authorised_url):
        '''
        Attempts to open a url which requires login and returns nothing if not logged in
        '''
        if self.browser and self._logged_in:
            response = self.browser.get(authorised_url)
            if response.url == authorised_url:
                return response.text;

        self._logged_in = False;
        return ""

    def _get_balance_page(self):
        if SpendingTracker.DEV:
            with open("balance.html", "r") as f:
                return str(f.read())
        else:
            return self._get_authorised_page(Api.BALANCE_URL)

    def _get_transactions_page(self):
        if SpendingTracker.DEV:
            with open("transactions.html", "r") as f:
                return str(f.read())
        else:
            return self._get_authorised_page(Api.TRANSACTIONS_URL)

    def __money_string_to_float(self, money_string):
        return float(money_string.split(" ")[0].replace(",", ""))

    def get_recent_transactions(self):
        '''
        Parses the transaction page for the last 10 transactions and returns them
        as transaction objects,

        returns empty of not logged in or couldn't connect
        '''

        transactions = []
        if self._logged_in:
            page = self._get_transactions_page()
            if page != "":
                soup = BeautifulSoup(page)
                for row in soup.find("table", id="txtable1").tbody:
                    if row.find('td') != -1:
                        cells = row.findAll('td')

                        time = dateutil.parser.parse(cells[0].getText()).timestamp()

                        type_place_text = cells[3].getText()
                        type_place_split = " ".join(type_place_text.strip().split("\n")[0].split()).split(" - ")

                        if (len(type_place_split) < 2):
                            # Not a transaction
                            continue

                        type_string, place = type_place_split

                        if type_string == "Purchase":
                            transaction_type = Transaction.TYPE_PURCHACE
                        elif type_string == "Withdrawal":
                            transaction_type = Transaction.TYPE_WITHDRAWAL
                        else:
                            transaction_type = Transaction.TYPE_UNKNOWN
                            print("Unknown transaction type: " + type_string)

                        amount = self.__money_string_to_float(cells[4].getText().strip())

                        transactions.append(Transaction(time, place, amount, transaction_type))
        else:
            return Api.ERROR_LOGGED_OUT

        # On the page transactions are in the wrong order
        return list(reversed(transactions))

    def get_balance(self):
        if self._logged_in:
            page = self._get_balance_page()
            if page != "":
                return self.__money_string_to_float(
                    page.split('<div class="balanceTotal">')[1].split("</div>")[0].strip()
                )
        else:
            return Api.ERROR_LOGGED_OUT
        return None


class SpendingTracker:
    DEV = False
    def __init__(self):
        locale.setlocale(locale.LC_ALL,'en_US.UTF-8')

        if SpendingTracker.DEV:
            self._api = Api("0", "0", "0", "0") # Todo
        else:
            self._api = Api(input("userid: "),
                            input("password: "),
                            input("security message: "),
                            input("security answer: "))
        self.__email = input("Email?: ")
        self.__email_password = input("Email password?: ")
        self._mail_server = input("Server?: ")

        if self._api.login():
            self._bank_account = BankAccount(self._api.get_user_id())
            self._bank_account.load_attributes()

            self.main_loop()
            print("Error in main loop, exiting")
        else:
            print("Initial login error")

    def send_transaction_email(self, transactions, balance):
        try:
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

            print("Sending email: ")
            print(content)

            msg = MIMEText(content, 'plain')
            msg['Subject'] = "CashPassport update - Balance : " + '{:,.2f}'.format(balance) + " EUR"
            msg['From'] = self.__email  # some SMTP servers will do this automatically, not all

            conn = SMTP(self._mail_server)
            conn.set_debuglevel(True)
            conn.login(self.__email, self.__email_password)
            conn.sendmail(self.__email, self.__email, msg.as_string())
            conn.quit()

        except Exception as exc:
            sys.exit("mail failed; %s" % str(exc))  # give a error message

    def main_loop(self):
        while True:
            # Check the account balance to see if it has changed
            old_balance = self._bank_account.get_balance()
            balance = self._api.get_balance()

            if balance == Api.ERROR_LOGGED_OUT and not self._api.is_logged_in():
                if self._api.login():
                    balance = self._api.get_balance()
                    if balance == Api.ERROR_LOGGED_OUT and not self._api.is_logged_in():
                        print("Error getting balance")
                        return
                else:
                    print("Login error")
                    return

            if balance != old_balance:
                print("New balance: " + str(balance))
                self._bank_account.set_balance(balance)

            recent_transactions = self._api.get_recent_transactions()
            new_transactions = []

            if recent_transactions == Api.ERROR_LOGGED_OUT:
                if self._api.login():
                    recent_transactions = self._api.get_recent_transactions()
                    if recent_transactions == Api.ERROR_LOGGED_OUT:
                        print("Error getting recent transactions")
                        return
                else:
                    print("Login error")
                    return

            for transaction in recent_transactions:
                if not self._bank_account.has_transaction(transaction):
                    new_transactions.append(transaction)
                    self._bank_account.new_transaction(transaction)

            if new_transactions:
                for transaction in new_transactions:
                    print("New transaction: ", transaction);

                self.send_transaction_email(new_transactions, balance)

            time.sleep(random.randint(30, 60)); # only refresh every 30-60 seconds
tracker = SpendingTracker()
