#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time
import random

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TEAMYELLOW"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

#POSITIONS

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

# ~~~~~============= OUR CODE ================~~~~~
def bonds(exchange, order_id):
		write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": "BOND", "dir": "BUY", "price": 999, "size": 10})
		time.sleep(.01)

		write_to_exchange(exchange, {"type": "add", "order_id": order_id + 1, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": 10})
		time.sleep(.01)

def adr(exchange, order_id, fair_value, spread):
		buyVal =int(fair_value - (spread / 2.0))
		sellVal =int(fair_value + (spread / 2.0))
		write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": "BABA", "dir": "BUY", "price": buyVal, "size": 1})
   
		write_to_exchange(exchange, {"type": "add", "order_id": order_id + 1, "symbol": "BABA", "dir": "SELL", "price" : sellVal, "size": 1})

def update_fair_value(e_msg, symbol):
		max_bid = 0
		min_offer = 99999999999999999
		bids = e_msg['buy']
		offers = e_msg['sell']
		for bid in bids:
				bid_val = bid[0]
				if (bid_val > max_bid):
						max_bid = bid_val
		for offer in offers:
				offer_val = offer[0]
				if (offer_val < min_offer):
						min_offer = offer_val
		print ("MAX BID: ", max_bid)
		print ("MIN OFFER: ", min_offer)
		return (max_bid + min_offer) / 2;

def get_spread(e_msg, symbol):
		max_bid = 0
		min_offer = 99999999999999999
		bids = e_msg['buy']
		offers = e_msg['sell']
 
		for bid in bids:
				bid_val = bid[0]
				if (bid_val > max_bid):
						max_bid = bid_val
		for offer in offers:
				offer_val = offer[0]
				if (offer_val < min_offer):
						min_offer = offer_val

		print ("MAX BID: ", max_bid)
		print ("MIN OFFER: ", min_offer)
		return (min_offer - max_bid) 

def refreshPos(exchange):
		e_msg = read_from_exchange(exchange)
		if (e_msg['type'] == 'fill'):
				if (e_msg['symbol'] == 'BABZ'):
						if (e_msg['dir'] == 'BUY'):
								position += 1
						elif (e_msg['dir'] == 'SELL'):
								position -= 1
							

# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
		exchange = connect()
		write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
		hello_from_exchange = read_from_exchange(exchange)
		print("The exchange replied:", hello_from_exchange, file=sys.stderr)
		# -------------------------------------------------------------------
		order_id = 0
		babz_fv = 0
		baba_fv = 0
		position = 0

		while True:
				bonds(exchange, order_id)
				order_id += 2

				refreshPos(exchange)

				if(position == 10):
						write_to_exchange(exchange, {"type": "convert", "order_id": order_id + 1, "symbol": "BABA", "dir": "SELL", "size": 10})
						order_id +=1000
						position = 0

				elif(position == -10):
						write_to_exchange(exchange, {"type": "convert", "order_id": order_id + 1, "symbol": "BABA", "dir": "BUY", "size": 10})
						order_id+=1000
						position = 0

				e_msg = read_from_exchange(exchange)
				if (e_msg['type'] == 'book'):
						if (e_msg['symbol'] == 'BABZ'):
								babz_fv = update_fair_value(e_msg, 'BABZ')
								print("BABZ FAIR VALUE: ", babz_fv)

								babz_spread = get_spread(e_msg, 'BABZ')
								print('BABZ SPREAD: ', babz_spread)

								baba_spread = (babz_spread + 2) + 2

								adr(exchange, order_id, babz_fv, baba_spread)
								order_id += 2

								print(e_msg, file=sys.stderr)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!

if __name__ == "__main__":
		main()
