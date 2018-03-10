import os
import sys
import platform
import calendar
import dateutil.parser
import dateutil.tz

from datetime import timedelta
from datetime import datetime

from banking import Transaction, TransactionList

if platform.system() == "Android":
    '''
    This is a fix for kivy and beautiful soup
    '''

    old_meta_path = sys.meta_path

    class ImportFixer(object):
        def __init__(self, mname):
            self.mname = mname

        def find_module(self, name, path=None):
            if name == self.mname:
                return self
            else:
                return
            return None

        def load_module(self, name):
            import _htmlparser as module
            module.__name__ = name
            return module

    sys.meta_path = [ImportFixer('bs4.builder._htmlparser')]

    # Now we have fixed the import we import BS4
    from bs4 import BeautifulSoup
    try:
        import mechanicalsoup
    except ImportError:
        sys.meta_path = old_meta_path
        import mechanicalsoup
else:
    from bs4 import BeautifulSoup
    import mechanicalsoup

MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(MAIN_PATH, "test_pages")):
    os.mkdir(os.path.join(MAIN_PATH, "test_pages"))

def normal_print(message):
    print(message)


def to_utc_timestamp(date_time):
    return calendar.timegm(date_time.utctimetuple())


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
    # time_zone
    #################
    try:
        with open(os.path.join(MAIN_PATH, "credentials/credentials.conf"), "r") as creds_file:
            for credential in creds_file.readlines():
                credentials.append(credential.strip())
    except Exception as e:
        credentials = []
        print("Error in credentials file: " + str(e))

    return credentials

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

    ERROR_BAD_PASSWORD = 0
    ERROR_BAD_USER_ID = 1
    ERROR_BAD_SECURITY_MESSAGE = 2
    ERROR_BAD_SECURITY_ANSWER = 3

    ERROR_LOGGED_OUT = -200000

    ERROR_LOGIN_IN_PROGRESS = 5

    CONNECTION_ERROR = 28382

    STATE_IDLE = 0
    STATE_LOGGING_IN = 1

    def __init__(self, user_id, password, validation_message, security_answer, time_zone, dev=False, log_function=normal_print, logging = True):
        self.__logging__ = logging
        self.__DEV__ = dev

        def api_log(message):
            log_function("[API] "+ message)

        self.log = api_log

        self.__time_zone = dateutil.tz.gettz(time_zone)

        self.__user_id = user_id
        self.__password = password
        self.__validation_message = validation_message
        self.__security_answer = security_answer
        self.__logged_in_token = False

        self.browser = None

        self._state = CashpassportApi.STATE_IDLE

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

    def get_state(self):
        return self._state

    def login(self):
        if self._state == CashpassportApi.STATE_LOGGING_IN:
            return CashpassportApi.ERROR_LOGIN_IN_PROGRESS

        self._state = CashpassportApi.STATE_LOGGING_IN
        code = self._login()
        self._state = CashpassportApi.STATE_IDLE

        return code

    def _login(self):
        if self.__DEV__:
            self.__logged_in_token = "DUMMY"
            return self.__logged_in_token

        # Create a new session
        self.browser = mechanicalsoup.StatefulBrowser(soup_config={'features': 'html.parser'})

        # Rather them not know we are a bot
        self.browser.session.headers['User-Agent'] = \
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

        if self.__logging__:
            self.log("Logging in")

        # First present our login id
        try:
            self.browser.open(CashpassportApi.MAIN_PAGE_URL)
        except:
            return CashpassportApi.CONNECTION_ERROR

        csrfToken = self._get_cstfToken_from_page(self.browser.get_current_page())

        self.browser.select_form(CashpassportApi.LOGIN_FORM_ID)
        self.browser.get_current_form().form.append(
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )
        self.browser["userIdInput"] = self.__user_id # input username

        if self.__logging__:
            self.log("Submitting username")
        try:
            self.browser.submit_selected()
        except:
            return CashpassportApi.CONNECTION_ERROR

        # Verify it has the correct security message
        page = self.browser.get_current_page()

        found_message = page.find("div", class_="security_phrase_value")
        if self.__logging__:
            self.log("Security message loaded = " + found_message.text)

        if not found_message.text:
            return CashpassportApi.ERROR_BAD_USER_ID

        if found_message.text != self.__validation_message:
            if self.__logging__:
                self.log("Bad site, wrong security message")
            return CashpassportApi.ERROR_BAD_SECURITY_MESSAGE
        else:
            if self.__logging__:
                self.log("Page verified")

        # Verified page so type password
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

        try:
            self.browser.submit_selected()
            # Manually open the urls to verify login
            self.browser.open(CashpassportApi.VALIDATE_LOGIN_PAGE_URL)
        except:
            return CashpassportApi.CONNECTION_ERROR

        # Submit the security answer
        try:
            self.browser.select_form(CashpassportApi.SECURITY_FORM_ID)
        except mechanicalsoup.LinkNotFoundError:
            return CashpassportApi.ERROR_BAD_PASSWORD

        # Input the answer
        self.browser["securityAnswer"] = self.__security_answer

        # And fill in the csrf token
        self.browser.get_current_form().form.insert(
            0,
            self._create_csrfToken_input(
                self.browser.get_current_page()
            )
        )

        # Remove auto login from the form submission
        auto_login = self.browser.get_current_form().form.find_all("input", {"name": "autoLogonOption"})[0]
        auto_login["checked"] = "false"
        auto_login["value"] = "false"

        if self.__logging__:
            self.log("Submitting security answer")

        try:
            self.browser.submit_selected()
            self.browser.open(CashpassportApi.MAIN_PAGE_URL)
        except:
            return CashpassportApi.CONNECTION_ERROR

        if self.browser.get_current_page().find("a", href="/travelex/cardholder/chProfile.view"):
            if self.__logging__:
                self.log("Login successful")
            self.__logged_in_token = csrfToken
        else:
            self.__logged_in_token = None
            if self.__logging__:
                self.log("Login unsuccessful")
                self.log(self.browser.get_current_page().find_all("a"))
            return CashpassportApi.ERROR_BAD_SECURITY_ANSWER

        return self.__logged_in_token

    def is_logged_in(self):
        return self.__logged_in_token

    def logout(self):
        if self.__DEV__:
            self.__logged_in_token = None
            return True

        if self.is_logged_in():
            response = self.browser.open(CashpassportApi.LOGOUT_PAGE_URL)

            if self.__logging__:
                self.log("Logging out")

            if response.url == CashpassportApi.LOGIN_PAGE_URL:
                self.__logged_in_token = None
                return True
        return False

    def _get_authorised_page(self, authorised_url, post_data=None):
        '''
        Attempts to open a url which requires login and returns nothing if not logged in
        '''
        if self.browser and self.__logged_in_token:
            if post_data:
                response = self.browser.post(authorised_url, data=post_data)
            else:
                response = self.browser.get(authorised_url)

            if response.url == authorised_url:
                # Replace all non ascii characters with question marks
                return "".join([x if ord(x) < 128 else '?' for x in response.text]);

        self.__logged_in_token = None;
        return CashpassportApi.ERROR_LOGGED_OUT

    def _get_balance_page(self):
        if self.__DEV__:
            with open(os.path.join(MAIN_PATH, "test_pages/balance.html"), "r") as f:
                return str(f.read())
        else:
            page = self._get_authorised_page(CashpassportApi.BALANCE_URL)
            with open(os.path.join(MAIN_PATH, "test_pages/balance.html"), "w") as f:
                f.write(page)
            return page

    def _get_transactions_page(self, period=None):
        if self.__DEV__:
            with open(os.path.join(MAIN_PATH, "test_pages/transactions.html"), "r") as f:
                return str(f.read())
        else:
            if period:
                page = self._get_authorised_page(
                    CashpassportApi.TRANSACTIONS_URL,
                    {
                        "csrfToken": self.__logged_in_token,
                        "current": (period == "CURRENT"),
                        "acrossCycles": False,
                        "theme": "plain",
                        "prepaidCycle": period,
                    }
                )
            else:
                page = self._get_authorised_page(CashpassportApi.TRANSACTIONS_URL)

            with open(os.path.join(MAIN_PATH, "test_pages/transactions.html"), "w") as f:
                f.write(page)
            return page

    def _money_string_to_float(self, money_string):
        return float(money_string.split(" ")[0].replace(",", ""))

    def _parse_transactions(self, page):
        soup = BeautifulSoup(page, "html.parser")
        transactions = TransactionList()
        # There are 2 possible tables both with the same id
        for transactionTable in soup.findAll("table", id="txtable1"):
            for row in transactionTable.tbody:

                # And each row contains a transaction
                if row.find('td') != -1:
                    cells = row.findAll('td')

                    date_time_text = cells[0].getText()

                    verified = (cells[1].getText().lower() != "pending")

                    transaction_time = dateutil.parser.parse(date_time_text).replace(tzinfo=self.__time_zone)

                    # Unverified transactions seem to be behind by exactly 5 hours + whatever the UTC offset is.
                    # Probably a bug that has been around for years
                    if not verified:
                        transaction_time = transaction_time + timedelta(hours=(5 + transaction_time.utcoffset().total_seconds() / 3600))

                    # Turn the time string into epoch time
                    timestamp = to_utc_timestamp(transaction_time)

                    # Then we need to parse the place and type string
                    type_place_text = cells[3].getText()

                    # This character for some reason is always
                    # in the description after the transaction type
                    type_place_split = type_place_text.split(u'\xa0')

                    if (len(type_place_split) < 2):
                        # Some transactions are for example the initial deposit which don't really count
                        continue

                    type_string = "".join(type_place_split.pop(0).split())  # Take the first part of the split

                    # Takes the last part of the string, joins it all together, removes bad chacters,
                    # removes large spaces and new lines, turns it into ascii and then removes, more string
                    place = " ".join(" ".join(type_place_split).strip().split()) \
                        .replace(" more . . .", "") \
                        .replace(",", "")

                    if place.startswith("-"):
                        # Our place does not need to start with a dash
                        place = place[2:]

                    if not place:
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
        return transactions

    def get_transactions(self, from_ts=0):
        '''
        Parses the transaction page for all transactions until the given timestamp

        returns empty or not logged if it couldn't connect
        '''

        transactions = TransactionList()

        if self.__logged_in_token:

            # Download the recent transactions page
            recent_transactions_page = self._get_transactions_page()

            if recent_transactions_page != CashpassportApi.ERROR_LOGGED_OUT:
                # Find the list of all possible transaction page values
                periods = []

                if self.__logging__:
                    self.log("Checking history of transactions back to " + datetime.fromtimestamp(from_ts).isoformat())

                for option in BeautifulSoup(recent_transactions_page, "html.parser").find("select", id="prepaidCycle").findAll("option"):
                    if option["value"] != "":
                        periods.append(option["value"])

                for transaction in reversed(self._parse_transactions(recent_transactions_page)):
                    if transaction.get_epoch_time() >= from_ts:
                        transactions.append(transaction)
                    else:
                        self.log("Found all required transactions")
                        return transactions

                # The first page didn't have all the transactions we needed
                # so now we need to load all the pages
                transactions = TransactionList()

                # Go through all transactions until we hit the transaction we need to go up to

                i = 1
                for period in periods:
                    self.log("Reading transaction history page: " + str(i))
                    i += 1

                    transactions_page = self._get_transactions_page(period=period)

                    if transactions_page == CashpassportApi.ERROR_LOGGED_OUT:
                        return CashpassportApi.ERROR_LOGGED_OUT

                    for transaction in reversed(self._parse_transactions(transactions_page)):
                        if transaction.get_epoch_time() >= from_ts:
                            transactions.append(transaction)
                        else:
                            self.log("Collected all required transactions")
                            return transactions

                self.log("Finished looking through transaction")
            else:
                return CashpassportApi.ERROR_LOGGED_OUT
        else:
            return CashpassportApi.ERROR_LOGGED_OUT

        return transactions

    def get_balance(self):
        if self.__logged_in_token:
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
    transactions = api.get_transactions()
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