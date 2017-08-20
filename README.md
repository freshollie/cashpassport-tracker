# cashpassport-tracker

Track how and where I spend my cashpassport money.

This is a python script which logs into cashpassport and sends me email updates when I spend money.

I have wrapped the script in a kivy application in order to be able to run on my old android phone as a service.

The api module could be used by anyone to log into the banking and do what you want.

## Executing

Create a credentails file in `credentials/credentials.conf` as follows:

    user_id
    password
    login website verification message
    secuirty answer
    email to send from and to
    password for email
    smtp mail server

To execute in python: `python src/tracker.py`

## Building for android

After verifying it runs on your PC

`./build_android`

This will fail the first run, run it again and the build should work.

You should get a folder with an APK.

For yours specific android device you will need to change the build architecture of the app. So far only the default has been tested.

## Dependencies

- Python 2.7

- Linux

### Libraries

`sudo pip install kivy mechanicalsoup beautifulsoup4 python-for-android dateutil markdown`

`sudo apt-get install buildozer`

