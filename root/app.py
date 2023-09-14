import json
from flask import Flask, jsonify, request
import yfinance as yf
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return "You should not go here :("




# ----- for client to call ----- #



# ----- for rasa to call ----- #


# get stock information
# -- parameters --
# stock: the stock id (e.g. "9988.hk", "tsla")
# -- return --
# a list of stock info
# -- error messages --
# 1: no stock provided
# -- error messages in each element --
# 2: cannot connect to server(yahoo api server)
# 3: stock id not found
@app.route('/stock_info', methods=['POST'])
def stock_info():
    data = [s.upper() for s in request.json]
    # data: a list of stock names (uppercase)

    if len(data) == 0:
        return jsonify({
            'error': 1,
        })

    return_list = []
    tickers = yf.Tickers(' '.join(data))

    for stock_name in data:
        try:
            return_list.append(tickers.tickers[stock_name].info)
        except requests.exceptions.ConnectionError:
            return_list.append({
                'error': 2,
            })
        except requests.exceptions.HTTPError:
            return_list.append({
                'error': 3,
            })

    return jsonify(return_list)

#debug
# print(dir(yf.Ticker('9988.hk')))
# print('-'*8)
# print(yf.Ticker('9988.hk').financials)
