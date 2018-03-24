# Cashpassport Tracker

Transaction update notifier for Mastercards Cashpassport service

## About

Cashpassport is a Prepaid Card scheme run by Mastercard. The card is topped up with a foreign currency,
to be used in that country with no transaction fees.

The website to view transactions or balance, however, is very old and not very helpful.

I wrote a wrapper-api for cashpassports website ([cashpassport-api](https://github.com/freshollie/cashpassport-api/)) which
this service uses to pull new transactions and issue an update email of any changes.

Credentials for the tracker are required to be stored in a postgres database ([cashpassport-db](https://github.com/freshollie/cashpassport-db/))

The service is designed to run alongside a frontend (Still being built). 

## Requirements

- Python 3.5

- cashpassport-api

- cashpassport-db

- Optional: docker

## Setup

`docker build -t cashpassport-tracker:master`

or

`python3 setup.py develop`

## Executing

The service is designed to execute for as many cashpassport accounts as required, configured
by adding them to the accounts table.

1. Add a user with email to the `users` table of cashpassport-db
1. Add the required credentials into the `accounts` table of cashpassport-db, along with `notify` as true
1. `python3 src/tracker.py [ARGS]`

Args can be found with `python3 src/tracker.py -h`

See more in `stack/docker-compose.yml`

## Standalone Build

Previously this service had the API built in and was designed to run on it's own without a DB.

This service could be built for android and so could run on an old smartphone.

Find this version under the tag `v1.1-standalone`
