import os
import json
import random
from flask import Flask, jsonify, request
import urllib.request
import requests
from bs4 import BeautifulSoup
import nasdaqdatalink as nasdaq
import talib
import numpy as np
import pandas as pd

from utils import *
from global_var import *




PORT = os.environ.get('FLASK_RUN_PORT')






# set tokens
nasdaq.ApiConfig.api_key = tokens['nasdaq']




app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'api': True,
    })




# ----- for client to call ----- #


# get unique ID for new user
# -- return --
# the new user ID (string)

# for api test
# localhost:5000/get_new_id
@app.route('/get_new_id', methods=['GET', 'POST'])
def get_new_id():
    return jsonify({
        'userID': str(users_col.insert_one({}).inserted_id),
    })






# ----- for rasa to call ----- #


# get real time stock information
# -- parameters --
# stocks: a list of stock ids (e.g. ["9988.hk", "0008.hk"])
# -- return --
# a list of stock info
# -- error messages --
# 1: no stock provided
# -- error messages in each element of the return list --
# 2: cannot connect to server
# 3: stock id not found

# for api test
# localhost:5000/stock_info
# {"stocks": ["9988.hk", "0008.hk"]}
@app.route('/stock_info', methods=['POST'])
def stock_info():
    json_data = request.json
    symbols = json_data['stocks']
    data = [yf_to_aa(s) for s in symbols]


    if len(data) == 0:
        return jsonify({
            'error': 1,
        })

    return_list = []

    cookie_list = [
        'AADetailChart=P%7c6%2cT%7c1%2cV%7ctrue%2cB%7c3%2cD%7c1%2cDP%7c10%7e20%7e50%7e100%7e150%2cL1%7c2%7e14%2cL2%7c3%7e12%7e26%7e9%2cL3%7c12%2cCO%7c1%2cCT%7c%2cCS%7c%2cSP%7c%2cAHFT%7ctrue; DetailChartDisplay=3; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; CookiePolicyCheck=0; __utmc=177965731; __utmz=177965731.1698675532.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmc=81143559; __utmz=81143559.1698675532.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _ga=GA1.1.1497994407.1698675532; NewChart=Mini_Color=1; __utma=177965731.377915610.1698675532.1698675532.1698677691.2; __utma=81143559.2140254432.1698675532.1698675532.1698677691.2; AALTP=1; aa_cookie=158.132.155.19_49311_1698681158; __utmt_a3=1; __utmb=177965731.11.10.1698677691; __utmt_a2=1; __utmt_b=1; __utmb=81143559.22.10.1698677691; _ga_FL2WFCGS0Y=GS1.1.1698677686.2.1.1698679752.0.0.0; _ga_38RQTHE076=GS1.1.1698677686.2.1.1698679752.0.0.0',
        'aa_cookie=42.2.152.85_54005_1698895454; CookiePolicyCheck=0; _ga=GA1.1.260176329.1698899757; AALTP=1; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; NewChart=Mini_Color=1; _ga_FL2WFCGS0Y=GS1.1.1698899757.1.1.1698899828.0.0.0; _ga_38RQTHE076=GS1.1.1698899757.1.1.1698899828.0.0.0',
        'aa_cookie=44.236.48.177_30931_1699012196; mLang=TC; CookiePolicyCheck=0; _ga=GA1.1.1282790483.1699016505; __utma=177965731.1282790483.1699016505.1699016505.1699016505.1; __utmc=177965731; __utmz=177965731.1699016505.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmt_a3=1; AALTP=1; _ga_MW096YVQH9=GS1.1.1699016514.1.0.1699016522.0.0.0; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; NewChart=Mini_Color=1; AAWS2=; __utmb=177965731.4.10.1699016505; __utma=81143559.1282790483.1699016505.1699016523.1699016523.1; __utmc=81143559; __utmz=81143559.1699016523.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt_a2=1; __utmt_b=1; __utmb=81143559.2.10.1699016523; _ga_FL2WFCGS0Y=GS1.1.1699016504.1.1.1699016522.0.0.0; _ga_38RQTHE076=GS1.1.1699016504.1.1.1699016522.0.0.0',
    ]

    for stock_name, symbol in zip(data, symbols):
        url = f'http://www.aastocks.com/tc/stocks/quote/detail-quote.aspx?symbol={stock_name}'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
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
                temp = soup.find('div', {'class': 'ind_ETF'})
                if temp:
                    # etf
                    stock_type = 'etf'
                else:
                    stock_type = 'stock'

                current_price = float(soup.find('div', {'id': 'labelLast'}).text.strip())
                
                prev_close_price, open_price = (float_or_none(x.strip()) for x in soup.find('div', {'id': 'valPrevClose'}).text.split('/', 1))
                
                temp = soup.find('div', {'id': 'valRange'}).text
                if 'N/A' in temp:
                    day_low = None
                    day_high = None
                else:
                    day_low, day_high = (float(x.strip()) for x in temp.split('-'))
                
                stock_number_per_hand = int(soup.find('div', string='每手股數').parent.find('div', {'class': 'float_r'}).text.strip())
                
                temp = soup.find('div', {'data-key': 'EPS'})
                earnings_per_share = temp and float(temp.parent.parent.find('div', {'class': 'float_r'}).text.strip())
                
                temp = soup.find('div', {'id': 'tbPERatio'})
                price_to_earnings_ratio, price_to_earnings_ratio_ttm = (float_or_none(x.strip()) for x in temp.find('div', {'class': 'float_r'}).text.split('/')) if temp else (None, None)

                temp = soup.find('div', {'id': 'tbPBRatio'})
                price_to_book_ratio, net_asst_value_per_share = (float(x.strip()) for x in temp.find('div', {'class': 'float_r'}).text.split('/')) if temp else (None, None)
                
                temp = soup.find('div', {'id': 'VolumeValue'})
                volumn = float(''.join((x.strip() for x in temp.find_all(string=True, recursive=False))))
                unit = temp.find('span', {'class': 'unit'}).text.strip()
                volumn = remove_unit(volumn, unit)

                temp = soup.find('div', string='成交金額').parent.find('div', {'class': 'cls'})
                turnover = float(''.join((x.strip() for x in temp.find_all(string=True, recursive=False))))
                unit = temp.find('span', {'class': 'unit'}).text.strip()
                turnover = remove_unit(turnover, unit)

                avg_price = float_or_none(soup.find('div', string='均價').parent.find('div', {'class': 'float_r'}).text.strip())

                temp = soup.find('div', {'data-key': 'Dividend Payout'})
                temp = temp and temp.parent.parent.find('div', {'class': 'float_r'}).text
                if not temp or 'N/A' in temp:
                    dividend_payout = None
                    dividend_per_share = None
                else:
                    temp = temp.split('/')
                    dividend_payout = float(temp[0].strip().strip('%').replace(',', '')) / 100
                    dividend_per_share = float(temp[1].strip())



                temp = soup.find('div', {'data-key': 'Dividend Yield'}).parent.parent.parent.find('div', {'class': 'float_r'}).text
                if 'N/A' in temp:
                    dividend_yield = None
                    dividend_yield_ttm = None
                else:
                    dividend_yield, dividend_yield_ttm = (float_or_none(x.strip().strip('%')) / 100 for x in temp.split('/'))
                
                temp = soup.find('div', string='巿值').parent.find('div', {'class': 'float_r'}).text.strip()

                market_value, unit = extract_num_unit(temp)
                market_value = remove_unit(market_value, unit)

                temp = float_or_none(soup.find('div', {'data-key': 'Turnover Rate'}).parent.parent.parent.find('div', {'class': 'float_r'}).text.strip().strip('%'))
                turnover_rate = temp and temp / 100

                ex_dividend_date = soup.find('div', {'data-key': 'Ex-dividend Date'}).parent.parent.find('div', {'class': 'float_r'}).text.strip() or None
                
                dividend_date = soup.find('div', string='派息日期').parent.find('div', {'class': 'float_r'}).text.strip() or None

                return_list.append({
                    'stockType': stock_type,
                    'symbol': symbol,
                    'currentPrice': current_price,
                    'previousClose': prev_close_price,
                    'open': open_price,
                    'dayLow': day_low,
                    'dayHigh': day_high,
                    'stockNumberPerHand': stock_number_per_hand,
                    'earningsPerShare': earnings_per_share,
                    'priceToEarningsRatio': price_to_earnings_ratio,
                    'priceToEarningsRatioTTM': price_to_earnings_ratio_ttm,
                    'dividendYield': dividend_yield,
                    'dividendYieldTTM': dividend_yield_ttm,
                    'volumn': volumn,
                    'turnover': turnover,
                    'avgPrice': avg_price,
                    'priceToBookRatio': price_to_book_ratio,
                    'netAsstValuePerShare': net_asst_value_per_share,
                    'marketValue': market_value,
                    'dividendPayout': dividend_payout,
                    'dividendPerShare': dividend_per_share,
                    'turnoverRate': turnover_rate,
                    'exDividendDate': ex_dividend_date,
                    'dividendDate': dividend_date,
                })
            except AttributeError as e:
                print(f'ERROR({symbol}): {e}')
                if '找不到股票代號' in result:
                    return_list.append({
                        'symbol': symbol,
                        'error': 3,
                    })
                else:
                    return_list.append({
                        'symbol': symbol,
                        'error': 2,
                    })
            except ValueError as e:
                # maybe cause by 暫停買賣
                print(f'ERROR({symbol}): {e}')
                return_list.append({
                    'symbol': symbol,
                    'error': 3,
                })
        except requests.exceptions.ConnectionError as e:
            print(f'ERROR({symbol}): {e}')
            return_list.append({
                'symbol': symbol,
                'error': 2,
            })


    return jsonify(return_list)




# get answer of qa
# -- parameters --
# qs: a list of questions
# -- return --
# a list of qas
# -- error messages --
# 1: no qs provided
# -- error messages in each element of the return list --
# 2: question not found

# for api test
# localhost:5000/qa
# {"qs": ["按金", "按盤價"]}
@app.route('/qa', methods=['POST'])
def qa():
    json_data = request.json
    qs = json_data['qs']


    if len(qs) == 0:
        return jsonify({
            'error': 1,
        })

    return_list = []

    result = None

    for q in qs:
        result = qa_col.find_one({'q': q}, {'_id': 0})
        if result:
            return_list.append(result)
        else:
            return_list.append({
                'q': q,
                'error': 2,
            })

    return jsonify(return_list)




# get technical analysis(TA) results
# -- parameters --
# stocks: a list of stock ids (e.g. ["9988.hk", "0607.hk"])
# -- return --
# a list of TA results
# -- error messages --
# 1: no stock provided
# -- error messages in each element of the return list --
# 2: cannot connect to server
# 3: stock id not found

# for api test
# localhost:5000/ta
# {"stocks": ["9988.hk"]}
@app.route('/ta', methods=['POST'])
def ta():
    json_data = request.json
    yf_list = json_data['stocks']
    aa_list = [yf_to_aa(s) for s in yf_list]


    if len(aa_list) == 0:
        return jsonify({
            'error': 1,
        })

    return_list = []

    for yf, aa in zip(yf_list, aa_list):
        result = ta_col.find_one({'symbol': yf, 'lastUpdate': {'$gte': get_current_date()}})
        if result:
            return_list.append(result)
            continue

        try:
            data = nasdaq.get(f'HKEX/{aa}')
        except nasdaq.errors.data_link_error.NotFoundError:
            return_list.append({
                'symbol': yf,
                'error': 3,
            })
            continue

        data['Close'] = data['Previous Close'].shift(-1)
        data.dropna(subset = ['Close'], inplace=True)
        data['Adj Close'] = data['Close']
        url = f"http://localhost:{PORT}/stock_split"
        headers = {}
        payload = {'stocks': [yf]}
        try:
            result = requests.post(
                url, timeout=40, headers=headers, json=payload, verify=False
            ).text

            result_json = json.loads(result)
            if type(result_json[yf]) != list and result_json[yf].get('error'):
                if result_json[yf].get('error') == 2:
                    return_list.append({
                        'symbol': yf,
                        'error': 3,
                    })
                    continue

            split_dividend_list = sorted(result_json[yf], key=lambda d: d['date'], reverse=True)
            for datum in split_dividend_list:
                if len(data.loc[:datum['date']]) > 0 and datum['splitDividend'] == 'split':
                    data.loc[:datum['date'], ['Nominal Price', 'High', 'Low', 'Adj Close']] *= datum['rate']
                    data.drop(data.loc[:datum['date']].index[-1], inplace=True)
                elif len(data.loc[:datum['date']]) > 0 and datum['splitDividend'] == 'dividend':
                    if datum['date'] == str(data.loc[:datum['date']].iloc[-1].name)[:10]:
                        last_date = data.loc[:datum['date']].iloc[-2].name
                    else:
                        last_date = data.loc[:datum['date']].iloc[-1].name
                    nominal_price = float(data.loc[last_date, 'Nominal Price'])
                    price_rate = 1-(datum['rate']/nominal_price)
                    data.loc[:last_date, ['High', 'Low', 'Adj Close']] *= price_rate
                    data.drop(last_date, inplace=True)

            # handle nan in High and Low
            data['High'] = np.where(data['High'].isnull(), data['Adj Close'], data['High'])
            data['Low'] = np.where(data['Low'].isna(), data['Adj Close'], data['Low'])

            last_update = get_current_datetime()
            last_date = data.iloc[-1].name

            # TA
            data['upperband'], data['middleband'], data['lowerband'] = talib.BBANDS(data['Adj Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            data['macd'], data['macdsignal'], data['macdhist'] = talib.MACD(data['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)
            data['rsi'] = talib.RSI(data['Adj Close'], timeperiod=14)

            # TA: signal and position
            data['boll_signal'] = np.where(data['High'] > data['upperband'], -1, 0)
            data['boll_signal'] = np.where(data['Low'] < data['lowerband'], 1, data['boll_signal'])
            data['macd_position'] = np.where(data['macdhist'] >= 0, 1, 0)
            data['macd_signal'] = np.where(data['macd_position'] > data['macd_position'].shift(1), 1, 0)
            data['macd_signal'] = np.where(data['macd_position'] < data['macd_position'].shift(1), -1, data['macd_signal'])
            data['rsi_signal'] = np.where(data['rsi'] > 70, -1, 0)
            data['rsi_signal'] = np.where(data['rsi'] < 30, 1, data['rsi_signal'])
            boll_current = 0
            rsi_current = 0
            boll_list = []
            rsi_list = []
            for i in range(len(data)):
                if data.iloc[i]['boll_signal'] == 1:
                    boll_current = 1
                elif data.iloc[i]['boll_signal'] == -1:
                    boll_current = 0
                boll_list.append(boll_current)

                if data.iloc[i]['rsi_signal'] == 1:
                    rsi_current = 1
                elif data.iloc[i]['rsi_signal'] == -1:
                    rsi_current = 0
                rsi_list.append(rsi_current)
            data = data.assign(boll_position = boll_list)
            data = data.assign(rsi_position = rsi_list)

            # TA: strategy
            data['log_return'] = np.log(data['Adj Close'] / data['Adj Close'].shift(1))
            data['boll_strategy'] = data['boll_position'].shift(1) * data['log_return']
            data['macd_strategy'] = data['macd_position'].shift(1) * data['log_return']
            data['rsi_strategy'] = data['rsi_position'].shift(1) * data['log_return']

            # strategy only calculate last year
            last_year_date = get_current_date() + datetime.timedelta(days=-365)
            data.loc[:last_year_date, 'log_return'] = 0
            data.loc[:last_year_date, 'boll_strategy'] = 0
            data.loc[:last_year_date, 'macd_strategy'] = 0
            data.loc[:last_year_date, 'rsi_strategy'] = 0

            last_week_date = get_current_date() + datetime.timedelta(days=-7)
            macd_date, macd_signal = None, 0
            for index, row in data.loc[last_week_date:].iterrows():
                if row['macd_signal'] != 0:
                    macd_date = index
                    macd_signal = row['macd_signal']
            ta = {
                'backtest': None if len(data) == len(data[last_year_date:]) else {
                    'boll': np.exp(data['boll_strategy'].sum()) - 1,
                    'macd': np.exp(data['macd_strategy'].sum()) - 1,
                    'rsi': np.exp(data['rsi_strategy'].sum()) - 1,
                },
                'signal': {
                    'boll': {
                        'signal': int(data.iloc[-1].boll_signal),
                        'upperband': data.iloc[-1].upperband,
                        'lowerband': data.iloc[-1].lowerband,
                    },
                    'macd': {
                        'signal': int(macd_signal),
                        'date': macd_date,
                    },
                    'rsi': {
                        'signal': int(data.iloc[-1].rsi_signal),
                        'value': data.iloc[-1].rsi,
                    },
                },
                'stock_return': np.exp(data['log_return'].sum()) - 1,
            }

            #DEBUG
            # data.iloc[-252:].to_csv('test.csv', sep=',', encoding='utf-8')

            # save to DB
            to_return = {
                'symbol': yf,
                'lastUpdate': last_update,
                'lastDate': last_date,
                'ta': ta,
            }
            ta_col.insert_one(to_return)

            return_list.append(to_return)
        except requests.exceptions.ConnectionError as e:
            print(f'ERROR({yf}): {e}')
            return_list.append({
                'symbol': yf,
                'error': 2,
            })

    return parse_json(return_list)





# save users' stock to database
# -- parameters --
# an object of the buying/selling stock information
# -- return --
# an object with error number
# -- error messages --
# 0: no error

# for api test
# localhost:5000/save_portfolio
# {"userID": "Sender", "buysell": "buy", "date": "2000/01/01", "price": 12.34, "stock": "0001.hk", "stockNumber": 100}
@app.route('/save_portfolio', methods=['POST'])
def save_portfolio():
    json_data = request.json
    user_id = json_data['userID']
    buysell = json_data['buysell']
    date = json_data['date']
    price = json_data['price']
    stock = json_data['stock']
    stock_number = json_data['stockNumber']

    error = 0

    portfolio_col.insert_one({
        'userID': user_id,
        'buysell': buysell,
        'date': date,
        'price': price,
        'stock': stock,
        'stockNumber': stock_number,
    })

    return jsonify({
        'error': error,
    })





# view users' current portfolio
# -- parameters --
# userID, [date]
# -- return --
# an object with current stock number for each stock
# e.g. {"0001.hk": 2000, "0002.hk": 500}

# for api test
# localhost:5000/current_portfolio
# {"userID": "Sender"}
# {"userID": "Sender2", "date": "2023-10-29"}
# {"userID": "Sender2", "date": "2023-10-30"}
# {"userID": "Sender2", "date": "2023-12-04"}
# {"userID": "Sender2", "date": "2023-12-04", "ignoreLastSplit": true}
@app.route('/current_portfolio', methods=['POST'])
def current_portfolio():
    json_data = request.json

    user_id = json_data['userID']
    date = json_data.get('date')
    date = date if date else format_date(get_current_date())
    ignore_last_split = json_data.get('ignoreLastSplit') == True

    actions = {}
    print(ignore_last_split)
    for result in portfolio_col.find({'userID': user_id}, sort=[("_id", 1)]):
        if not result.get('stock') in actions:
            actions[result.get('stock')] = []
        actions[result.get('stock')].append(result)

    return_dict = {x: 0 for x in actions.keys()}
    url = f"http://localhost:{PORT}/stock_split"
    headers = {}
    payload = {'stocks': list(actions.keys())}
    try:
        result = requests.post(
            url, timeout=40, headers=headers, json=payload, verify=False
        ).text

        result_json = json.loads(result)
        if result_json.get('error') == 1:
            # cannot connect to aastocks server
            print('ERROR: Cannot connect to AASTOCKS server.')
        for stock in result_json.keys():
            if type(result_json[stock]) != list and result_json[stock].get('error') == 2:
                # stock ID not found
                continue

            for datum in result_json[stock]:
                if datum['splitDividend'] == 'split':
                    actions[stock].append({
                        'buysell': 'split',
                        'date': datum['date'],
                        'rate': datum['rate'],
                    })

            actions[stock].sort(key=lambda x: (x['date'], x['buysell']))
            for action in actions[stock]:
                if action['date'] > date:
                    break

                if action.get('buysell') == 'buy':
                    return_dict[stock] += action.get('stockNumber')
                elif action.get('buysell') == 'sell':
                    return_dict[stock] -= action.get('stockNumber')
                elif action.get('buysell') == 'split':
                    if not (ignore_last_split and action.get('date') == date):
                        return_dict[stock] /= action.get('rate')
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({stock}): {e}')

    return jsonify(return_dict)










# ----- for self call ----- #
# for api test
# localhost:5000/get_recommend

@app.route('/get_recommend', methods=['POST'])
def get_recommend():
    return_list = []
    result = None
    cookie_list = [
        'ASP.NET_SessionId=l3vwkyjyoeipxofgwclo5p45; aa_cookie=1.65.157.151_49759_1706423235; CookiePolicyCheck=0; _ga_FL2WFCGS0Y=GS1.1.1706427746.1.0.1706427746.0.0.0; _ga=GA1.1.1373671240.1706427747; __utma=177965731.1373671240.1706427747.1706427747.1706427747.1; __utmc=177965731; __utmz=177965731.1706427747.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_a3=1; __utmb=177965731.1.10.1706427747; __utma=81143559.1373671240.1706427747.1706427747.1706427747.1; __utmc=81143559; __utmz=81143559.1706427747.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_b=1; __utmb=81143559.1.10.1706427747; _ga_38RQTHE076=GS1.1.1706427747.1.0.1706427747.0.0.0',
    ]

    url = f'http://www.aastocks.com/tc/ltp/RTAI.aspx?type=1'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list),
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text

        soup = BeautifulSoup(result, features='html.parser')

        anchor = soup.find_all("table", width="99%")
        print (len(anchor))
        if not anchor:
            # stock not found
            return jsonify({
                'error': 2,
            })
        for table in anchor:
            recommend_list=[]
            x=table.find_all("table","pickL")
            print (len(x))
            for table in x:
                y=table.find("a")
                print (y.text.split()[-1])
                recommend_list.append(y.text.split()[-1])
            return_list.append(recommend_list)
        
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })

    return jsonify(return_list)


# get stock split/dividend
# -- parameters --
# stocks: list of stock ids
# -- return --
# dict of list of stock split/dividend info
# -- error messages --
# 1: cannot connect to server
# -- error messages in each element of the return dict --
# 2: stock id not found

# for api test
# localhost:5000/stock_split
# {"stocks": ["0001.hk", "0607.hk"]}
@app.route('/stock_split', methods=['POST'])
def stock_split():
    json_data = request.json
    stocks = json_data['stocks']

    return_dict = {}

    cookie_list = [
        'aa_cookie=1.65.201.178_57487_1703743573; mLang=TC; CookiePolicyCheck=0; __utma=177965731.1037720175.1703741287.1703741287.1703741287.1; __utmc=177965731; __utmz=177965731.1703741287.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmt_a3=1; _ga=GA1.1.886609921.1703741287; _ga_MW096YVQH9=GS1.1.1703741302.1.0.1703741302.0.0.0; AALTP=1; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; NewChart=Mini_Color=1; AAWS2=; __utma=81143559.886609921.1703741287.1703741304.1703741304.1; __utmc=81143559; __utmz=81143559.1703741304.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt_a2=1; __utmt_b=1; _ga_FL2WFCGS0Y=GS1.1.1703741286.1.1.1703741411.0.0.0; _ga_38RQTHE076=GS1.1.1703741286.1.1.1703741412.0.0.0; __utmb=177965731.18.10.1703741287; __utmb=81143559.10.9.1703741366373',
        'aa_cookie=58.153.154.84_63748_1708533945; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; CookiePolicyCheck=0; _ga=GA1.1.1298668379.1708509818; __utma=177965731.1298668379.1708509818.1708509818.1708509818.1; __utmc=177965731; __utmz=177965731.1708509818.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_a3=1; __utmb=177965731.1.10.1708509818; __utma=81143559.1298668379.1708509818.1708509818.1708509818.1; __utmc=81143559; __utmz=81143559.1708509818.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_a2=1; __utmb=81143559.1.10.1708509818; _ga_FL2WFCGS0Y=GS1.1.1708509817.1.0.1708509825.0.0.0; _ga_38RQTHE076=GS1.1.1708509818.1.0.1708509825.0.0.0',
    ]

    stock_name = None
    result = None
    url = None
    headers = None
    return_list = None
    for symbol in stocks:
        return_list = []
        return_dict[symbol] = return_list
        stock_name = yf_to_aa(symbol)
        result = split_col.find_one({'symbol': symbol, 'lastUpdate': {'$gte': get_current_date()}})
        if result:
            return_dict[symbol] = result.get('data')
            continue

        url = f'http://www.aastocks.com/tc/stocks/analysis/dividend.aspx?symbol={stock_name}'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
            'Host': 'www.aastocks.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }
        try:
            result = requests.get(
                url, timeout=40, headers=headers, verify=False
            ).text

            soup = BeautifulSoup(result, features='html.parser')

            anchor = soup.find("td", text="派息日")
            if not anchor:
                # stock not found
                return_dict[symbol] = {
                    'error': 2,
                }
                continue

            table = anchor.find_parent('table')

            rows = table.find_all('tr')
            for row in rows[1:]:
                split_dividend = None
                rate = None
                cols = row.find_all('td')
                detail = cols[3].text.strip().replace('：', ':').replace(': ', ':')
                date = cols[5].text.strip().replace('/', '-')
                
                if date == '-':
                    continue
                if detail.startswith('普通股息') or detail.startswith('特別股息'):
                    split_dividend = 'dividend'
                    if '相當於港元' in detail:
                        temp_str = ''
                        for c in detail[detail.index('相當於港元')+5:].strip():
                            if c in ('0123456789.'):
                                temp_str += c
                            else:
                                break
                        rate = float(temp_str)
                    else:
                        try:
                            temp_str = ''
                            for c in detail[detail.index('港元')+2:].strip():
                                if c in ('0123456789.'):
                                    temp_str += c
                                else:
                                    break
                            rate = float(temp_str)
                        except ValueError:
                            try:
                                temp_str = ''
                                for c in detail[detail.index('美元')+2:].strip():
                                    if c in ('0123456789.'):
                                        temp_str += c
                                    else:
                                        break
                                rate = float(temp_str)
                            except:
                                temp_str = ''
                                for c in detail[detail.index('人民幣')+3:].strip():
                                    if c in ('0123456789.'):
                                        temp_str += c
                                    else:
                                        break
                                rate = float(temp_str)
                elif detail.startswith('合併'):
                    split_dividend = 'split'
                    numerator = int(detail[detail.index(':')+1:detail.index('股合併')].strip())
                    denominator = int(detail[detail.index('合併為')+3:-1].strip())
                    rate = numerator / denominator
                elif detail.startswith('分拆'):
                    split_dividend = 'split'
                    numerator = int(detail[detail.index(':')+1:detail.index('股拆')].strip())
                    denominator = int(detail[detail.index('股拆')+2:-1].strip())
                    rate = numerator / denominator
                elif detail.startswith('股份拆細'):
                    split_dividend = 'split'
                    numerator = int(detail[detail.index(':')+1:detail.index('股拆')].strip())
                    denominator = int(detail[detail.index('股拆')+2:-1].strip())
                    rate = numerator / denominator
                else:
                    continue

                if split_dividend != None and rate != None:
                    return_list.append({
                        'date': date,
                        'splitDividend': split_dividend,
                        'rate': rate,
                    })

            last_update = get_current_datetime()

            # save to DB
            to_return = {
                'symbol': symbol,
                'lastUpdate': last_update,
                'data': return_list,
            }
            split_col.insert_one(to_return)
        except requests.exceptions.ConnectionError as e:
            print(f'ERROR({symbol}): {e}')
            return jsonify({
                'error': 1,
            })

    return parse_json(return_dict)






# wrapper of rasa api
# -- parameters --
# sender: the unique user ID
# message: the message of the sender
# -- return --
# return what rasa api return directly
# e.g.
# [{
#     "recipient_id": "Sender",
#     "text": "\u963f\u91cc\u5df4\u5df4\uff0d\uff33\uff37(09988) \u7684\u73fe\u50f9\u662f 71.3\u3002"
# }]
# -- error messages --
# 1: cannot connect to server


# get stock EPS/年度收入增長
# -- parameters --
# stock: stock id (e.g. "9988.hk"/"0008.hk")
# -- return --
# a list of stock EPS/年度收入增長
# -- error messages --
# 1: cannot connect to server
# 2: stock id not found

# for api test
# localhost:5000/get_future
# {"stock": "09988.hk"}
@app.route('/get_future', methods=['POST'])
def get_future():
    json_data = request.json
    symbol = json_data['stock']
    stock_name = yf_to_aa(symbol)
    return_list = []

    result = None
    cookie_list = [
        f'MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; AAWS=; __utmz=177965731.1706548775.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/company-fundamental/; _ga=GA1.1.1111401661.1706548779; mLang=TC; CookiePolicyCheck=0; __utma=177965731.867252439.1706548775.1706632264.1706709816.3; __utmc=177965731; __utmc=81143559; cto_bundle=GzvXhl9uYnFKcWxpQzBSbTZ3ckRsMkR1SVpCMEhqeks5YVk2ZHR6VnhJOGxORmdCQ3dPS3JvaHklMkJTS1p5MlMlMkZaazMxTUN1bGtNWDFlbVEya2V4R1JBN1RTOWs4RmRLV0dhYWZOcUVEZm4wVDFhTXE0TXV0NmtJQjJtQnlSZkprM3JsS0dvcHpmanE0Uk9yb0hOQVZ1TUJ2Z2dBJTNEJTNE; _ga_MW096YVQH9=GS1.1.1706710420.1.0.1706710420.0.0.0; NewChart=Mini_Color=1; __utmt_a3=1; __utma=81143559.1648372063.1706548775.1706709838.1706712121.4; __utmz=81143559.1706712121.4.2.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; __utmt_a2=1; __utmt_b=1; aa_cookie=27.109.218.9_63070_1706714877; __gads=ID=0554592d72201b43:T=1706548776:RT=1706712517:S=ALNI_MYAXodkQ_RUUnwvogWLuzRAOgsIRw; __gpi=UID=00000cf386237f10:T=1706548776:RT=1706712517:S=ALNI_MbCipQTizyo4ttg4DkAGd2qduIiIw; __eoi=ID=0eb93aed36a03300:T=1706632265:RT=1706712517:S=AA-AfjZlC4icUga4POBjQvB5Cqef; __utmb=177965731.18.10.1706709816; __utmb=81143559.18.10.1706712121; _ga_FL2WFCGS0Y=GS1.1.1706709817.3.1.1706712630.0.0.0; _ga_38RQTHE076=GS1.1.1706709819.17.1.1706712631.0.0.0',
    ]

    url = f'http://www.aastocks.com/tc/stocks/analysis/company-fundamental/earnings-summary?symbol={stock_name}&period=4'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text
    
    #finding the revenue
        soup = BeautifulSoup(result, features='html.parser')
        anchor =soup.select('td.cfvalue.txt_r.cls.bold')
        last_year_revenue = anchor[1].text.strip()
        if(anchor[1].previous_sibling.previous_sibling.text.strip()=="盈利(百萬)"or "-"):
            two_year_revenue = "N/A"
            three_year_revenue = "N/A"
        else:
            two_year_revenue =anchor[1].previous_sibling.previous_sibling.text.strip()
            if(anchor[1].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()=="盈利(百萬)"or "-"):
                three_year_revenue = "N/A"
            else:
                three_year_revenue = anchor[1].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()
        if(last_year_revenue[0]=='-'):
            last_year_revenue=last_year_revenue[1:]
            last_year_revenue=float(last_year_revenue)*(-1)
        if(last_year_revenue[0]=='-'):
            two_year_revenue=two_year_revenue[1:]
            two_year_revenue=float(two_year_revenue)*(-1)
        if(three_year_revenue[0]=='-'):
            three_year_revenue=three_year_revenue[1:]
            three_year_revenue=float(three_year_revenue)*(-1)
        print(last_year_revenue)
        print(two_year_revenue)
        print(three_year_revenue)
        print("----------------")

    #finding EPS of the stock
        soup = BeautifulSoup(result, features='html.parser')
        anchor =soup.select('td.cfvalue.txt_r.cls.bold')
        last_year_EPS = anchor[2].text.strip()
        if(anchor[2].previous_sibling.previous_sibling.text.strip()=="每股盈利"):
            two_year_EPS = "N/A"
        else:
            two_year_EPS =anchor[2].previous_sibling.previous_sibling.text.strip()
            if(anchor[2].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()=="每股盈利"):
                three_year_EPS = "N/A"
            else:
                three_year_EPS = anchor[2].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()
        print(last_year_EPS)
        print(two_year_EPS)
        print(three_year_EPS)
        print("----------------")
        if not anchor:
            # stock not found
            return jsonify({
                'error': 2,
            })

    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })

    result = None
    cookie_list = [
        f'MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; AAWS=; __utmz=177965731.1706548775.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/company-fundamental/; __utmz=81143559.1706548775.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/company-fundamental/; _ga=GA1.1.1111401661.1706548779; aa_cookie=223.16.119.164_51789_1706705282; mLang=TC; CookiePolicyCheck=0; __utma=177965731.867252439.1706548775.1706632264.1706709816.3; __utmc=177965731; __utmt_a3=1; __utmb=177965731.2.10.1706709816; __utma=81143559.1648372063.1706548775.1706632264.1706709838.3; __utmc=81143559; __utmt_a2=1; __utmt_b=1; __utmb=81143559.2.10.1706709838; _ga_FL2WFCGS0Y=GS1.1.1706709817.3.1.1706709838.0.0.0; _ga_38RQTHE076=GS1.1.1706709819.17.1.1706709838.0.0.0; __gads=ID=0554592d72201b43:T=1706548776:RT=1706709839:S=ALNI_MYAXodkQ_RUUnwvogWLuzRAOgsIRw; __gpi=UID=00000cf386237f10:T=1706548776:RT=1706709839:S=ALNI_MbCipQTizyo4ttg4DkAGd2qduIiIw; __eoi=ID=0eb93aed36a03300:T=1706632265:RT=1706709839:S=AA-AfjZlC4icUga4POBjQvB5Cqef; cto_bundle=GzvXhl9uYnFKcWxpQzBSbTZ3ckRsMkR1SVpCMEhqeks5YVk2ZHR6VnhJOGxORmdCQ3dPS3JvaHklMkJTS1p5MlMlMkZaazMxTUN1bGtNWDFlbVEya2V4R1JBN1RTOWs4RmRLV0dhYWZOcUVEZm4wVDFhTXE0TXV0NmtJQjJtQnlSZkprM3JsS0dvcHpmanE0Uk9yb0hOQVZ1TUJ2Z2dBJTNEJTNE',
    ]
    url = f'http://www.aastocks.com/tc/stocks/analysis/peer.aspx?symbol={stock_name}&t=6&hk=0'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text

       
        soup = BeautifulSoup(result, features='html.parser')

        anchor = soup.find('div', text="市盈率")
        if (anchor.find_next_sibling().text.strip()=='N/A'):
            PE_ratio="N/A"        
        else:
            PE_ratio=float(anchor.find_next_sibling().text.strip())
        print(PE_ratio)
        if not anchor:
            # stock not found
            return jsonify({
                'error': 2,
            })

    #finding annual revenue growth
        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('table',{'id': 'tblTS2'})
        x=anchor.find_all('td',{'class':'txt_r'})
        i=0
        annual_revenue_growth_list=[]
        while i+1< len(x):
            while i%10==2:
                annual_revenue_growth_list.append(x[i].text.split())
                i = i + 1
            i = i + 1

        if not anchor:
            # stock not found
            return jsonify({
                'error': 2,
            })    
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })

    
    result = None
    cookie_list = [
        f'AAWS=; _ga=GA1.1.1111401661.1706548779; mLang=TC; NewChart=Mini_Color=1; AAWS2=; MasterSymbol={stock_name}; LatestRTQuotedStocks=02477%3B02511%3B09988; __utmz=177965731.1707041168.9.5.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; CookiePolicyCheck=0; __utma=177965731.867252439.1706548775.1707041168.1707381172.10; __utmc=177965731; AALTP=1; _ga_MW096YVQH9=GS1.1.1707381174.5.0.1707381174.0.0.0; __utma=81143559.1648372063.1706548775.1707041168.1707381176.11; __utmc=81143559; __utmz=81143559.1707381176.11.9.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/; aa_cookie=65.181.65.72_5981_1707378871; __utmt_a3=1; __utmt_a2=1; __utmt_b=1; __gads=ID=0554592d72201b43:T=1706548776:RT=1707384352:S=ALNI_MYAXodkQ_RUUnwvogWLuzRAOgsIRw; __gpi=UID=00000cf386237f10:T=1706548776:RT=1707384352:S=ALNI_MbCipQTizyo4ttg4DkAGd2qduIiIw; __eoi=ID=0eb93aed36a03300:T=1706632265:RT=1707384352:S=AA-AfjZlC4icUga4POBjQvB5Cqef; __utmt_edu=1; cto_bundle=ysOOLF9uYnFKcWxpQzBSbTZ3ckRsMkR1SVpQUnNrVGxRRUJYODglMkI1MzJNd3JvUlYlMkZ6YUVNSW4yRkJGVGJ2R3F3ZUNhMVA1d2RRb3NkcndMbjJhUFgwY21nTmxzZEVuQUNUSnNTVURJWEhpJTJCbHVTVm51OXFIMFdEVm9BOFRueExoOEw2VmFOVzM4RWNPdFRlOWZLTm1XbEl1bFElM0QlM0Q; __utmb=177965731.26.10.1707381172; __utmb=81143559.52.9.1707384466426; _ga_FL2WFCGS0Y=GS1.1.1707381172.11.1.1707384552.0.0.0; _ga_38RQTHE076=GS1.1.1707381172.25.1.1707384553.0.0.0',
    ]
    url = f'http://www.aastocks.com/tc/stocks/analysis/peer.aspx?symbol={stock_name}'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text
    # find pe and pb ratio
        pe_ratio_list=[]
        pb_ratio_list=[]
        import test
        for data in test.my_list:
            pe_ratio_list.append(data.split(":")[1].split("&")[0].strip())
            pb_ratio_list.append(data.split("&")[1].strip())
        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('table',{'id': 'tblTS2'})
        x=anchor.find_all('td',{'class':'txt_r'})
        if not anchor:
                # stock not found
                return jsonify({
                    'error': 2,
                })
        i=0
        while i+1<len(x):
            while i%9==5:
                pe_ratio_list.append(x[i].text.strip().replace("[", "").replace("]", ""))
                pb_ratio_list.append(x[i+1].text.strip().replace("[", "").replace("]", ""))
                i = i + 1
            i = i + 1
        
        temp_pe_ratio_list = []
        for pe_ratio in pe_ratio_list:
            if pe_ratio=="無盈利"or pe_ratio== "N/A":
                temp_pe_ratio_list.append(99999)
            else:
                temp_pe_ratio_list.append(float(pe_ratio.strip()))
        print(temp_pe_ratio_list)
        temp_pb_ratio_list = []
        for pb_ratio in pb_ratio_list:
            if  pb_ratio=="N/A":
                pass
            else:
                temp_pb_ratio_list.append(float(pb_ratio.strip()))

        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('table',{'id': 'tblTS2'})
        x=anchor.find_all('td',{'class':'txt_r'})
        # to change 
        soup = BeautifulSoup(result, features='html.parser')
        link=f"/tc/stocks/quote/detail-quote.aspx?symbol={stock_name}"
        print(link)
        anchor = soup.find('a',{'href': link})
        print(anchor)
        target_number = anchor.find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().text.strip()
        sorted_numbers = sorted(temp_pe_ratio_list)  # Sort the list in ascending order
        pe_ratio_rank = sorted_numbers.index(target_number) +1  # minus 1 to get the rank (1-based indexing)
        print(pe_ratio_rank)     
        print(len(temp_pe_ratio_list))
        # to change  
        target_number = 1.39
        sorted_numbers = sorted(temp_pb_ratio_list)  # Sort the list in ascending order
        pb_ratio_rank = sorted_numbers.index(target_number) +1  # minus 1 to get the rank (1-based indexing)
        print(pb_ratio_rank)     
        print(len(temp_pb_ratio_list))

        result = None
    cookie_list = [
        f'mLang=TC; _ga=GA1.1.1464946004.1708264002; NewChart=Mini_Color=1; AAWS2=; AAWS=; CookiePolicyCheck=0; MasterSymbol={stock_name}; LatestRTQuotedStocks=00001%3B00004%3B00005%3B02511%3B09988; __utmc=177965731; AALTP=1; _ga_MW096YVQH9=GS1.1.1709130890.6.0.1709130890.0.0.0; __utmc=81143559; aa_cookie=61.15.99.24_64375_1709136045; __utma=177965731.780197868.1708264002.1709130889.1709134710.9; __utmz=177965731.1709134710.9.4.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; __utmt_a3=1; __utma=81143559.1464946004.1708264002.1709130891.1709134710.9; __utmz=81143559.1709134710.9.9.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; __utmt_a2=1; __gads=ID=a9c009372c39cc84:T=1708264000:RT=1709134710:S=ALNI_MZAZTfN92pZOHyH9ksQpYursfF0-w; __gpi=UID=00000d09af28c7df:T=1708264000:RT=1709134710:S=ALNI_MYip_3NSn44fhZa_br93obuxL_W1g; __eoi=ID=2b67c1fcdaf92edd:T=1708264000:RT=1709134710:S=AA-AfjYNMLYr5qwpNPB_dHIlFob8; _ga_FL2WFCGS0Y=GS1.1.1709134708.10.1.1709134895.0.0.0; __utmb=177965731.4.10.1709134710; __utmb=81143559.4.10.1709134710; _ga_38RQTHE076=GS1.1.1709134708.10.1.1709134895.0.0.0; cto_bundle=FZj6EV9HenJaM3JWanRLQUVLaFdieG1kUEhmV3p1NHZOSUJuUmFOTUhuNmM3WE5EMGFjTEdraHFRR2hYWjd2RkFUVVNnZHRucDFSMFFKaVkwcGUlMkZoNXVEUHR6JTJGeTglMkJNbkhXWk5LVTVrTVpXdG1JRSUyQmZubWV2VzRrTXowT2JyTm1Cd3BKVlN0TURlcldZN1BYJTJCQjRpQ2xOV1pBJTNEJTNE',
    ]
    url = f'http://www.aastocks.com/tc/stocks/analysis/company-fundamental/profit-loss?symbol={stock_name}'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list).format(stock_name = stock_name),
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text

      ### if pe_ratio_rank != None and rate != None:
               # return_list.append({
                   # 'date': date,
                   # 'splitDividend': split_dividend,
                   # 'rate': rate,
              #  })
        #if not anchor:
            # stock not found
           # return jsonify({
               # 'error': 2,
            #})
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })



    return jsonify(return_list)

# for api test
# localhost:5000/rasa
# {"sender": "Sender", "message": "阿里股價幾多？" }
@app.route('/rasa', methods=['POST'])
def rasa():
    json_data = request.json
    # sender = json_data['sender']
    # message = json_data['message']


    url = f'{rasa_ip}/webhooks/rest/webhook'
    headers = {}
    payload = json_data
    try:
        result = requests.post(
            url, timeout=40, headers=headers, json=payload, verify=False
        ).text

        to_return = json.loads(result)
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR: {e}')
        to_return = {
            'error': 1,
        }


    return parse_json(to_return)









#debug (if here stop, server will hang)
# print(yf_to_aa('9988.hk'))
