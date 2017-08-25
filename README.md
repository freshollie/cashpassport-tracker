# cashpassport-tracker
Track how and where I spend my cashpassport money.

This is a python script which logs into CashPassport coperate webserver and sends me email updates when I spend money.

I have wrapped the script in a Kivy Python Application in order to be able to run on my old android phone as a Service.

The api module could be used by anyone to log into the banking and do what you want.

## Executing

Create a credentails file in `credentials/credentials.conf` as follows:

    user_id
    password
    login website verification message
    secuirty answer
    email to send from
    password for email
    smtp mail server
    email to send to

To execute in native python: `python src/tracker.py`

To execute as a kivy application: `python src/main.py`

## Building for android

After verifying it runs on your PC

`./build_android.sh`

You should get a bin folder with the APK

For yours specific android device you will need to change the build architecture of the app. So far only the default has been tested.

## Dependencies

- Python 2.7

- Linux

### Libraries

`sudo pip install kivy mechanicalsoup beautifulsoup4 python-for-android dateutil markdown`

`sudo apt-get install buildozer`

