import os
import sys
from datetime import timedelta

'''
This is a fix for kivy and beautiful soup
'''
class ImportFixer(object):
    def __init__(self, mname):
        self.mname = mname

    def find_module(self, name, path=None):
        if name == self.mname:
            return self
        return None

    def load_module(self, name):
        import _htmlparser as module
        module.__name__ = name
        return module

sys.meta_path = [ImportFixer('bs4.builder._htmlparser')]

# Now we have fixed the import we import BS4
from bs4 import BeautifulSoup

import dateutil.parser
import mechanicalsoup
import time

from banking import Transaction, TransactionList


def normal_print(message):
    print message

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

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

class CashpassportApi:
    '''
    Simple HTML parsing api which can send all the required information to log in,
    gather transaction details, and balance amounts from the cashpassport website.

    Seeing as this is probably completely against the terms of service of the site,
    I wouldn't execute this often. The site was build a very long time ago so they
    probably won't notice bot requests, but probably not worth being banned for.

    USE AT YOUR OWN RISK
    '''

    LOGIN_PAGE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/public/app/registeredCardholderLogin"
    LOGOUT_PAGE_URL = "https://cardholder.mastercardworldwide.com/travelex/cardholder/public/app/logout"

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

    def __init__(self, user_id, password, validation_message, security_answer, dev = False, log_function=normal_print, logging = True):
        self.__logging__ = logging
        self.log = log_function
        self.__DEV__ = dev;
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
        Returns the cstf token from the page by parsing the javascript
        '''
        return page.text.split('var sessionSynchronizationToken = "')[1].split('"')[0]

    def login(self):

        if self.__DEV__:
            self._logged_in = True
            return self._logged_in

        # Create a new session
        self.browser = mechanicalsoup.StatefulBrowser()

        # Rather them not know we are a bot
        self.browser.session.headers['User-Agent'] = \
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

        if self.__logging__:
            self.log("Logging in")

        # First present out login id
        self.browser.open(CashpassportApi.MAIN_PAGE_URL)
        self.browser.select_form(CashpassportApi.LOGIN_FORM_ID)
        self.browser.get_current_form().form.append(
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )
        self.browser["userIdInput"] = self.__user_id # input username

        if self.__logging__:
            self.log("Submitting username")
        self.browser.submit_selected()

        # Verify it has the correct security message
        page = self.browser.get_current_page()
        if self.__logging__:
            self.log("Security message loaded = " + page.find("div", class_="security_phrase_value").text)

        if page.find("div", class_="security_phrase_value").text != self.__validation_message:
            if self.__logging__:
                self.log("Bad site, wrong security message")
            return False
        else:
            if self.__logging__:
                self.log("Page verified")

        # Verified page so typing password
        self.browser.select_form(CashpassportApi.PASSWORD_FORM_ID)
        self.browser["password"] = self.__password # Input the password
        self.browser.get_current_form().form["action"] = "/pkmslogin.form"
        self.browser.get_current_form().form.append(
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )
        # self.browser["action"] = "/pkmslogin.form"
        if self.__logging__:
            self.log("Submitting password")
        self.browser.submit_selected()

        # Manually open the urls to verify login
        self.browser.open(CashpassportApi.VALIDATE_LOGIN_PAGE_URL)

        # Submit the security answer
        self.browser.select_form(CashpassportApi.SECURITY_FORM_ID)
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

        if self.__logging__:
            self.log("Submitting security answer")
        self.browser.submit_selected()
        self.browser.open(CashpassportApi.MAIN_PAGE_URL)

        if self.browser.get_current_page().find("a", href="/travelex/cardholder/chProfile.view"):
            if self.__logging__:
                self.log("Login successful")
            self._logged_in = True
        else:
            self._logged_in = False
            if self.__logging__:
                self.log("Login unsuccessful")
                self.log(self.browser.get_current_page().find_all("a"))

        return self._logged_in

    def is_logged_in(self):
        return self._logged_in

    def logout(self):
        if self.__DEV__:
            self._logged_in = False
            return True

        if self.is_logged_in():
            response = self.browser.open(CashpassportApi.LOGOUT_PAGE_URL)
            if response.url == CashpassportApi.LOGIN_PAGE_URL:
                self._logged_in = False
                return True
        return False

    def _get_authorised_page(self, authorised_url):
        '''
        Attempts to open a url which requires login and returns nothing if not logged in
        '''
        if self.browser and self._logged_in:
            response = self.browser.get(authorised_url)
            if response.url == authorised_url:
                return response.text;

        self._logged_in = False;
        return CashpassportApi.ERROR_LOGGED_OUT

    def _get_balance_page(self):
        if self.__DEV__:
            with open(os.path.join(MAIN_PATH, "test_pages/balance.html"), "r") as f:
                return str(f.read())
        else:
            return self._get_authorised_page(CashpassportApi.BALANCE_URL)

    def _get_transactions_page(self):
        if self.__DEV__:
            with open(os.path.join(MAIN_PATH, "test_pages/transactions.html"), "r") as f:
                return str(f.read())
        else:
            page = self._get_authorised_page(CashpassportApi.TRANSACTIONS_URL)
            #with open(os.path.join(MAIN_PATH, "test_pages/transactions.html"), "w") as f:
                #f.write(page)
            return page

    def _money_string_to_float(self, money_string):
        return float(money_string.split(" ")[0].replace(",", ""))

    def get_recent_transactions(self):
        '''
        Parses the transaction page for the last 10 transactions and returns them
        as transaction objects,

        returns empty of not logged in or couldn't connect
        '''

        transactions = TransactionList()
        if self._logged_in:
            page = self._get_transactions_page()
            if page != CashpassportApi.ERROR_LOGGED_OUT:
                soup = BeautifulSoup(page)

                # There are 2 possible tables both with the same id
                for transactionTable in soup.findAll("table", id="txtable1"):
                    for row in transactionTable.tbody:

                        # And each row contains a transaction
                        if row.find('td') != -1:
                            cells = row.findAll('td')

                            date_time_text = cells[0].getText()

                            verified = (cells[1].getText().lower() != "pending")

                            transaction_time = dateutil.parser.parse(date_time_text)

                            # Unverified transactions seem to be behind by exactly 7 hours.
                            # Probably a bug that has been around for years
                            if not verified:
                                transaction_time = transaction_time + timedelta(hours=7)

                            # Turn the time string into epoch time
                            timestamp = time.mktime(transaction_time.timetuple())

                            # Then we need to parse the place and type string
                            type_place_text = cells[3].getText()

                            # This character for some reason is always
                            # in the description after the transaction type
                            type_place_split = type_place_text.split(u'\xa0')

                            if (len(type_place_split) < 2):
                                # Some transactions are for example the initial deposit which don't really count
                                continue

                            type_string = "".join(type_place_split.pop(0).split()) # Take the first part of the split

                            # Takes the last part of the string, joins it all together, removes bad chacters,
                            # removes large spaces and new lines, turns it into ascii and then removes, more string
                            place = " ".join(" ".join(type_place_split).strip().split()).encode('ascii')\
                                .replace(" more . . .", "")

                            if (place.startswith("-")):
                                # Our place does not need to start with a dash
                                place = place[2:]

                            if (place == ""):
                                # Again, probably not a transaction, no place given
                                continue

                            # Convert the type name to its value
                            if type_string.lower() == "purchase":
                                transaction_type = Transaction.TYPE_PURCHACE
                            elif type_string.lower() == "withdrawal":
                                transaction_type = Transaction.TYPE_WITHDRAWAL
                            else:
                                transaction_type = Transaction.TYPE_UNKNOWN
                                if self.__logging__:
                                    self.log("Unknown transaction type: " + type_string)

                            amount = self._money_string_to_float(cells[4].getText().strip())

                            transactions.append(Transaction(timestamp, place, amount, transaction_type, verified))
            else:
                return CashpassportApi.ERROR_LOGGED_OUT
        else:
            return CashpassportApi.ERROR_LOGGED_OUT

        return transactions

    def get_balance(self):
        if self._logged_in:
            page = self._get_balance_page()

            if page != CashpassportApi.ERROR_LOGGED_OUT:
                return self._money_string_to_float(
                    page.split('<div class="balanceTotal">')[1].split("</div>")[0].strip()
                )
        return CashpassportApi.ERROR_LOGGED_OUT

def tests():
    DEV = True
    print("-" * 20)
    print("Starting API tests")

    print("-" * 20)
    print("Loading credentials")
    credentials = load_credentails()
    assert credentials, "Credentials not loaded properly"

    print("-" * 20)
    print("Initalising API")
    api = CashpassportApi(credentials[0], credentials[1], credentials[2], credentials[3], dev=DEV)
    assert api, "Api not loaded"

    print("-" * 20)
    print("Testing login")
    assert api.login() == True, "Login error"
    assert api._get_transactions_page() != CashpassportApi.ERROR_LOGGED_OUT, "Login failed to provide authorisation"

    print("-" * 20)
    print("Testing transaction list loading")
    transactions = api.get_recent_transactions()
    assert len(transactions) == 4, "Wrong number of transactions expected 4 got " + str(len(transactions))

    print(transactions)

    print("-" * 20)
    print("Testing balance loading")
    assert api.get_balance() > 3000, "Wrong balance"

    print("-" * 20)
    print("Checking logout")
    assert api.logout(), "Failed to logout"
    assert api.get_balance() == CashpassportApi.ERROR_LOGGED_OUT, "Logout didn't work properly"

    print("-" * 20)
    print("Tests completed successfully")

if __name__ == "__main__":
    tests()