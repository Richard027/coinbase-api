from prometheus_client import start_http_server, Histogram, Counter
from coinbase.wallet.error import CoinbaseError
from coinbase.wallet.client import Client
import time
import random
import string
import configparser
import os
import sys


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini'))
api_key = config.get('coinbase_api', 'api_key', fallback=False)
api_secret = config.get('coinbase_api', 'api_secret', fallback=False)

client = Client(
    api_key,
    api_secret,
    api_version='2017-12-02',
    )

c = Counter('coinbase_http_response_total', 'HTTP responses counted by status_code', ['method', 'code', 'message'])
req_time = Histogram('coinbase_request_seconds', 'Time spent processing request', ['method'])
get_accounts_time = req_time.labels(method='get_accounts')
update_user_time = req_time.labels(method='update_current_user')
request_money_time = req_time.labels(method='request_money')


@update_user_time.time()
def update_user_request():
    try:
        client.update_current_user(name=''.join(random.choice(string.ascii_lowercase) for i in range(10)))
        c.labels(method='update_current_user', code="200", message='ok').inc()
    except CoinbaseError as E:
        c.labels(method='update_current_user', code=E.status_code, message=E.id).inc()


@get_accounts_time.time()
def get_accounts_request():
    try:
        client.get_accounts()
        c.labels(method='get_accounts', code="200", message='ok').inc()
    except CoinbaseError as E:
        c.labels(method='get_accounts', code=E.status_code, message=E.id).inc()


@request_money_time.time()
def give_me_my_money_request():
    try:
        client.request_money(
            client.get_primary_account().id,
            to="blord@yandex.ru",
            amount="1",
            currency="BTC")
        c.labels(method='request_money', code="200", message='ok').inc()
    except CoinbaseError as E:
        c.labels(method='request_money', code=E.status_code, message=E.id).inc()


if __name__ == '__main__':
    port = 8000
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    start_http_server(port)

    while True:
        time.sleep(random.randint(3, 10))

        try:
            get_accounts_request()
            update_user_request()
            give_me_my_money_request()
        except Exception as E:
            sys.stderr.write('Unhandled Exception in client_id %s\n' % E)
            exit()