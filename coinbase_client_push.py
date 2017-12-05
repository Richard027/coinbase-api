from prometheus_client import Counter, Histogram, CollectorRegistry, push_to_gateway
from coinbase.wallet.error import CoinbaseError
from coinbase.wallet.client import Client
import time
import random
import string
import configparser
import os
import sys


forks = 2
if len(sys.argv) == 2:
    # we don't want to get banned
    if int(sys.argv[1]) < 6:
        forks = int(sys.argv[1])

for i in range(forks):
    try:
        pid = os.fork()
    except OSError:
        sys.stderr.write("Could not create a child process\n")
        continue

    if pid == 0:
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini'))
        api_key = config.get('coinbase_api', 'api_key', fallback=False)
        api_secret = config.get('coinbase_api', 'api_secret', fallback=False)
        prometheus_addr = config.get('prometheus_server', 'addr', fallback=False)

        client = Client(
            api_key,
            api_secret,
            api_version='2017-12-02',
            )

        random.seed()
        client_id = random.random()

        histogram_reg = CollectorRegistry()
        counter_reg = CollectorRegistry()

        c = Counter('coinbase_http_response_total', 'HTTP responses counted by status_code', ['client', 'method', 'code', 'message'], registry=counter_reg)
        req_time = Histogram('coinbase_request_seconds', 'Time spent processing request', ['client', 'method'], registry=histogram_reg)

        get_accounts_time = req_time.labels(client=client_id, method='get_accounts')
        update_user_time = req_time.labels(client=client_id, method='update_current_user')
        request_money_time = req_time.labels(client=client_id, method='request_money')


        @update_user_time.time()
        def update_user_request():
            try:
                client.update_current_user(name=''.join(random.choice(string.ascii_lowercase) for i in range(10)))
                c.labels(client=client_id, method='update_current_user', code="200", message='ok').inc()
            except CoinbaseError as E:
                c.labels(client=client_id, method='update_current_user', code=E.status_code, message=E.id).inc()


        @get_accounts_time.time()
        def get_accounts_request():
            try:
                client.get_accounts()
                c.labels(client=client_id, method='get_accounts', code="200", message='ok').inc()
            except CoinbaseError as E:
                c.labels(client=client_id, method='get_accounts', code=E.status_code, message=E.id).inc()


        @request_money_time.time()
        def give_me_my_money_request():
            try:
                client.request_money(
                    client.get_primary_account().id,
                    to="blord@yandex.ru",
                    amount="1",
                    currency="BTC")
                c.labels(client=client_id, method='request_money', code="200", message='ok').inc()
            except CoinbaseError as E:
                c.labels(client=client_id, method='request_money', code=E.status_code, message=E.id).inc()


        while True:
            time.sleep(random.randint(3, 10))

            try:
                get_accounts_request()
                update_user_request()
                give_me_my_money_request()

                push_to_gateway(prometheus_addr, job='api-test_pushgateway_%f' % client_id, registry=histogram_reg)
                push_to_gateway(prometheus_addr, job='counters_push_%f' % client_id, registry=counter_reg)
            except Exception as E:
                sys.stderr.write('Unhandled Exception: %s\n' % E)
                exit()

for _ in range(forks):
    os.waitpid(0, 0)
