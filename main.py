import mechanicalsoup
import sys
import time
import os
import hashlib

class Transaction:
    def __init__(self, time, place, amount):
        self.__time = time
        self.__place = place
        self.__amount = amount

    def get_hash(self):
        return hashlib.md5().update(self.__time + self.__place + self.__amount).hexdigest()

    def get_time(self):
        return self.__time

    def get_place(self):
        return self.__place

    def get_amount(self):
        return self.__amount

class BankAccount:
    def __init__(self, user, balance, transactions):
        self.__user = user
        self.__balance = balance
        self.__transactions = transactions
        self.load_transactions()

    def get_balance(self):
        return self.__balance

    def get_transactions(self):
        return self.__transactions

    def set_balance(self, balance):
        self.__balance = balance

    def set_transactions(self, transaction):
        self.__transactions = transaction

    def add_transaction(self, transaction):
        self.__transactions.append(transaction)

    def load_transactions(self):
        if (os.path.isfile(self.__user + "_account.txt")):
            with open(self.__user + "_account.txt", "r") as transactions_file:
                for line in transactions_file.readline():
                    if (line.strip() != ""):
                        # Tranactions are saved as time,place,amount in a txt
                        time, place, amount = line.strip().split(",")
                        continue

                    # If we got there then there is a blank line
                    # So the next line must be the transaction
                    balance_line = transactions_file.readline()
                    if (balance_line.strip() != "" and "," not in balance_line.strip()):
                        balance = tran


    def save_transactions(self):

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

    def __init__(self, user_id, password, validation_message, security_answer):
        self.__user_id = user_id
        self.__password = password
        self.__validation_message = validation_message
        self.__security_answer = security_answer
        self._logged_in = False;

        self.login()

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

    def _create_csrfToken_input(self, page):
        '''
        Direct port from the pages javascript

        Inserts the csrf token to the form for submitting
        '''
        token = self._get_cstfToken(page)

        input = page.new_tag("input")
        input['type'] = 'hidden'
        input['name'] = 'csrfToken'
        input['id'] = 'csrfToken'
        input['value'] = token
        input['defaultValue'] = token
        input['readonly'] = "readonly"

        return input

    def _get_cstfToken(self, page):
        '''
        Returns the cstf token from the page
        '''
        return page.text.split('var sessionSynchronizationToken = "')[1].split('"')[0]

    def login(self):
        # Create a new session
        self._logged_in = True
        return self._logged_in

        # Todo: Fix after all data algorithms done
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
        self.browser["securityAnswer"] = Api.__answer # Input the answer

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

    def _get_balance_page(self):
        with open("balance.html", "r") as f:
            return str(f.read())

            # Todo
            # return self._get_authorised_page(SpendingTracker.BALANCE_URL)

    def _get_transactions_page(self):
        with open("balance.html", "r") as f:
            return str(f.read())
        return self._get_authorised_page(SpendingTracker.TRANSACTIONS_URL)


class SpendingTracker:
    def __init__(self):
        self._api = Api(input("userid: "),
                        input("password: "),
                        input("security message: "),
                        input("security answer: "))

        self._bank_account = BankAccount(SpendingTracker.USER_ID)

    def main_loop(self):

tracker = SpendingTracker()
