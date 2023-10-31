import json
from flask import Flask, jsonify, request
import urllib.request
import requests
from bs4 import BeautifulSoup
from utils import *

app = Flask(__name__)

@app.route('/')
def index():
    return 'You should not go here :('




# ----- for client to call ----- #



# ----- for rasa to call ----- #


# get stock information
# -- parameters --
# stock: the stock id (e.g. "9988.hk")
# -- return --
# a list of stock info
# -- error messages --
# 1: no stock provided
# -- error messages in each element of the return list --
# 2: cannot connect to server
# 3: stock id not found

# for api test
# localhost:5000/stock_info
# {"stocks": ["9988.hk"]}
@app.route('/stock_info', methods=['POST'])
def stock_info():
    json_data = request.json
    data = [yf_to_aa(s) for s in json_data['stocks']]


    if len(data) == 0:
        return jsonify({
            'error': 1,
        })

    return_list = []

    for stock_name in data:
        url = f'http://www.aastocks.com/tc/stocks/quote/detail-quote.aspx?symbol={stock_name}'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': f'AADetailChart=P%7c6%2cT%7c1%2cV%7ctrue%2cB%7c3%2cD%7c1%2cDP%7c10%7e20%7e50%7e100%7e150%2cL1%7c2%7e14%2cL2%7c3%7e12%7e26%7e9%2cL3%7c12%2cCO%7c1%2cCT%7c%2cCS%7c%2cSP%7c%2cAHFT%7ctrue; DetailChartDisplay=3; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; CookiePolicyCheck=0; __utmc=177965731; __utmz=177965731.1698675532.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmc=81143559; __utmz=81143559.1698675532.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _ga=GA1.1.1497994407.1698675532; NewChart=Mini_Color=1; __utma=177965731.377915610.1698675532.1698675532.1698677691.2; __utma=81143559.2140254432.1698675532.1698675532.1698677691.2; AALTP=1; aa_cookie=158.132.155.19_49311_1698681158; __utmt_a3=1; __utmb=177965731.11.10.1698677691; __utmt_a2=1; __utmt_b=1; __utmb=81143559.22.10.1698677691; _ga_FL2WFCGS0Y=GS1.1.1698677686.2.1.1698679752.0.0.0; _ga_38RQTHE076=GS1.1.1698677686.2.1.1698679752.0.0.0',
            'Host': 'www.aastocks.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }
        try:
            result = requests.get(
                url, timeout=40, headers=headers, verify=False
            ).text

            soup = BeautifulSoup(result, features='html.parser')
            try:
                current_price = float(soup.find('div', {'id': 'labelLast'}).text.strip())
                return_list.append({
                    'currentPrice': current_price,
                })
            except AttributeError as e:
                print(e)
                if '對不起﹐找不到股票代號' in result:
                    return_list.append({
                        'error': 3,
                    })
                else:
                    return_list.append({
                        'error': 2,
                    })
        except requests.exceptions.ConnectionError as e:
            print(e)
            return_list.append({
                'error': 2,
            })


    return jsonify(return_list)

#debug (if here stop, server will hang)
# print(yf_to_aa('9988.hk'))
