#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import random
import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TEAMYELLOW"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

def trade_bonds(exchange, order_id):
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": "BOND", "dir": "BUY", "price": 999, "size": 100});
    order_id += 1
        
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": 100});

# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    # -------------------------------------------------------------------
    order_id = 0
    portfolio = {"BOND": 0, "BABZ": 0, "BABA": 0, "AAPL": 0, "MSFT": 0, "GOOG": 0, "XLK": 0}

    while True:
        e_msg = read_from_exchange(exchange)
        if (e_msg['type'] == 'fill'):
            if (e_msg['dir'] == 'BUY'):
                portfolio["BOND"] += 1
            elif (e_msg['dir'] == 'SELL'):
                portfolio["BOND"] -= 1
            print(e_msg, file=sys.stderr)
            print(portfolio)
        if (random.random() < .5):
            trade_bonds(exchange, order_id)
            order_id += 2
	
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!

if __name__ == "__main__":
    main()
