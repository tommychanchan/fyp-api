import json
from flask import Flask, jsonify, request
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def index():
    return "You should not go here :("




# ----- for client to call ----- #



# ----- for rasa to call ----- #


# get stock information
# -- parameters --
# stock: the stock id (e.g. "9988.hk", "tsla")
# -- return keys --
# currency: "HKG"/"USD"/"TWD"
# currentPrice: float
# -- error messages --
# 1: argument stock missing
# 2: stock id not found
@app.route('/stock_info')
def stock_info():
    stock = request.args.get('stock')
    if stock == None:
        return jsonify({
            'error': 1,
        })

    try:
        ticker = yf.Ticker(stock).info
    except:
        return jsonify({
            'error': 2,
        })


    return jsonify(ticker)

#debug
print(dir(yf.Ticker('9988.hk')))
print('-'*8)
print(yf.Ticker('9988.hk').financials)