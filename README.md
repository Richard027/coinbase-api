# Description #
**Python client for coinbase.com API**

It synchronically requests 3 different api methods from coinbase.com in an infinite loop and provides some metrics for prometheus system:
* histogram of each method
* total count of api responses divided by http_status_code (one method request is unsuccessful for this demo)

# Python client dependencies #
```
virtualenv -p /usr/bin/python3 ~/coinbase_env
source ~/coinbase_env/bin/activate
pip install coinbase prometheus-client
```
Also, patch for coinbase python library is available in "patches" directory. It resolves problem with unhandled json exceptions, e.g. caused by temporary banning.

# Running client #
Configure your coinbase api secrets and prometheus server at **settings.ini**

### In pull mode ###
`python coinbase_client.py [listen_port]`

Check result at http://localhost:[listen_port]

### In push mode ###
`python coinbase_client_push.py [forks_number_less_than_6]`

Check result at you prometheus pushgateway web interface
