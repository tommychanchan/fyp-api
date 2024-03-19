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
with open('stock_ids.json', 'r') as f:
    STOCK_IDS = json.load(f)


sample_stocks = [
    '騰訊控股',
    '阿里巴巴－ＳＷ',
    '盈富基金',
    '香港交易所',
    '中國海洋石油',
    '匯豐控股',
    '比亞迪股份',
    '中國移動',
    '快手－Ｗ',
]

sample_qas = [
    '蟹貨',
    '除淨日',
    'ETF',
    '交易所買賣基金',
    '即日鮮',
    '斬倉',
    '強制清盤',
    '碎股',
    '毛利率',
    '市盈率',
    'RSI',
    '簡單移動平均線',
    '保力加通道',
    'MACD',
    '毫子股',
    '共同基金',
    '股份回購',
    '風險披露書',
]

#股票資料
stock_info_qs = [
    # current price
    '{stock}現價幾多？',
    # previous close
    '{stock}收市價幾多？',
]

#股票分析
stock_analysis_qs = [
    # ta
    '{stock}基本面分析',
    '{stock}的基本分析',
    # fa
    '{stock}技術面分析',
    '從基本面分析{stock}',
    # ta+fa
    '{stock}值得投資嗎？',
    '幫我分析{stock}',
    '{stock}的分析',
]

#我的股票 - 未買入任何股票
my_stock_input_only_qs = [
    '我尋日買左1手{stock}，股價係30.0',
    '我2024/02/21買入了2手{stock}，股價是10.2',
    '我前日買左100股{stock}，買入價格是$62.25',
    '我2023/11/19買左2手{stock}，當時價格是4.78',
    '我2024/01/10買入了200股{stock}，當時股價是14.76',
]

#我的股票
my_stock_qs = [
    # input
    '我尋日買左1手{stock}，股價係70.0',
    '我2024/02/21買入了2手{stock}，股價是101.2',
    '我2024/03/12賣出了200股{stock}，當時股價是44.5',
    '我2023/11/28賣出了2手{stock}，賣出價格係$88.35',
    # 我的持倉
    '我的持倉',
    '我依家有咩股票係手？',
    '我2023/12/04的持倉',
    '我2024/03/19持有甚麼股票',
    # 交易記錄
    '交易記錄',
    '我的買賣記錄',
    # 盈虧
    '我的盈虧',
    '盈虧分析',
]

#財經入門
qa_qs = [
    '甚麼是{qa}？',
    '甚麼是{qa}',
    '乜野係{qa}？',
    '咩係{qa}',
    '{qa}是甚麼？',
    '{qa}係咩？',
]





# set tokens
nasdaq.ApiConfig.api_key = tokens['nasdaq']




app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'catbot': True,
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

    if to_return == []:
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
    weekend = get_current_datetime().weekday() > 4
    after1620 = get_current_datetime().time() > datetime.time(16, 20)
    for stock_name, symbol in zip(data, symbols):
        if weekend or after1620:
            result = real_time_col.find_one({'symbol': symbol, 'lastUpdate': {'$gte': get_current_date()}})
            if result:
                return_list.append(result)
                continue
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
                price_to_earnings_ratio, price_to_earnings_ratio_ttm = (float_or_none(x.strip()) if x.strip() != '無盈利' else '無盈利' for x in temp.find('div', {'class': 'float_r'}).text.split('/')) if temp else (None, None)

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

                last_update = get_current_datetime()

                to_return = {
                    'lastUpdate': last_update,
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
                }

                if weekend or after1620:
                    real_time_col.insert_one(to_return)

                return_list.append(to_return)
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


    return parse_json(return_list)




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
# {"qs": ["按金", "按盤價"]}
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
        data['Adj Close'] = data['Close']

        previous_close = None
        url = f"http://localhost:{PORT}/stock_info"
        headers = {}
        payload = {'stocks': [yf]}
        try:
            result = requests.post(
                url, timeout=40, headers=headers, json=payload, verify=False
            ).text

            result_json = json.loads(result)

            if len(result_json):
                previous_close = result_json[0].get('previousClose')
        except requests.exceptions.ConnectionError as e:
            print(f'ERROR({yf}): {e}')

        if previous_close:
            data.iloc[-1, data.columns.get_loc('Adj Close')] = previous_close
        else:
            data.dropna(subset = ['Close'], inplace=True)
        data.dropna(subset = ['Adj Close'], inplace=True)


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
# {"userID": "Sender", "buysell": "buy", "date": "2000-01-01", "price": 12.34, "stock": "0001.hk", "stockNumber": 100}
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
# userID, [date(today)], [ignoreLastSplit(false)]
# -- return --
# an object with current stock number for each stock up to certain date
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
    for result in portfolio_col.find({'userID': user_id}, sort=[("date", 1), ("buysell", 1)]):
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








# view users' transaction record
# -- parameters --
# userID
# -- return --
# actions: a list of transaction/split information

# for api test
# localhost:5000/transaction_record
# {"userID": "Sender"}
@app.route('/transaction_record', methods=['POST'])
def transaction_record():
    json_data = request.json

    user_id = json_data['userID']

    actions = [x for x in portfolio_col.find({'userID': user_id})]

    stocks = list({x.get('stock') for x in portfolio_col.find({'userID': user_id})})

    url = f"http://localhost:{PORT}/stock_split"
    headers = {}
    payload = {'stocks': stocks}
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
                    actions.append({
                        'buysell': 'split',
                        'date': datum['date'],
                        'rate': datum['rate'],
                        'stock': stock,
                    })

            actions.sort(key=lambda x: (x['date'], x['buysell']))
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({stock}): {e}')

    return parse_json({
        'actions': actions,
    })











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



# get latest index
# -- parameters --
# None
# -- return --
# A list of index, in the index list,which contain current stock price(float), change(float),change%(float),opening price(float),turnover(float),highest price(float), lowest price(float), and weekly price change(float)
# -- error messages --
# 1: cannot connect to server
# 2: stock id not found

# for api test
# localhost:5000/get_index
     
@app.route('/get_index', methods=['POST'])
def get_index():
    json_data = request.json
    symbol = json_data['stock']
    stock_name = yf_to_aa(symbol)
    return_list = []
    result = None
    cookie_list = [
        f'mLang=TC; _ga=GA1.1.1412667535.1709474457; NewChart=Mini_Color=1; AAWS2=; AAWS=; DetailChartDisplay=3; _cc_id=9542af56eef4e8e8d665aebe000f91ae; NewsZoomLevel=3; DynamicChart2=CPT=0&CPTS=&CPTM=&P=52&VB=1&CVB=1&CT=candles&T=dark&EP=1&EE=1&EAHFT=1&ES=0&DC=red&SPUP=1&ISQ=0&MI=SMA|10|20|50|100|150&TI1=Volume&TI2=RSI|14&TI3=MACD|12|26|9&TI4=&TI5=&H=300|100|100|100|null|null&ME=1|1|1|1|1&ConfigName=&ConfigID=1; SHMasterSymbol=603719; CNHK=BrowserHistory=603719.SH; _ga_JGELR0JK0N=GS1.1.1710170910.1.0.1710170919.0.0.0; LatestWarrantCbbc=26789%3B59345%3B14711; panoramaId=301586df4f9bdf722d764d902f444945a70264b20153567be835abff1d281e28; panoramaIdType=panoIndiv; AADetailChart=P%7c6%2cT%7c1%2cV%7ctrue%2cB%7c3%2cD%7c1%2cDP%7c10%7e20%7e50%7e100%7e150%2cL1%7c2%7e14%2cL2%7c3%7e12%7e26%7e9%2cL3%7c12%2cCO%7c1%2cCT%7c1%2cCS%7c%2cSP%7chide%2cAHFT%7ctrue; MasterSymbol=09988; LatestRTQuotedStocks=05545%3B04618%3B00308%3B00341%3B02099%3B03718%3B26789%3B59345%3B02477%3B14711%3B09633%3B09879%3B06990%3B08547%3B05641%3B02511%3B00988%3B00998%3B09888%3B09988; panoramaId_expiry=1711289610736; _ga_MW096YVQH9=GS1.1.1710684937.10.1.1710684985.0.0.0; aa_cookie=202.155.245.119_26245_1710824105; CookiePolicyCheck=0; __utmc=177965731; __utmc=81143559; BMPBrokerage=3/19/2024 12:16:54 PM; __utma=177965731.1232723388.1709474457.1710821648.1710821814.24; __utmz=177965731.1710821814.24.8.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utma=81143559.1412667535.1709474457.1710821648.1710821814.24; __utmz=81143559.1710821814.24.8.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); cto_bundle=b9u1-V8lMkZZanJuT01DZFM5cVFjMG5xc3N3U1Zsd3dJQklIWE9tTmdmcThNOFdiQ08zTlU4bEpEQlU3MXEyWnd2ZXBxOUh1JTJGVVAwM1JJdFRpWFE4TFFBdjV4S2g5T1BnektlcGw3RDRtSlEzQ0VSZTRtbFUyajlHUW1PSGtEWVg5eVJ4UDVqOTNFSVkxMll6NUNjRGRFJTJGdUR2b3clM0QlM0Q; __utmt_a3=1; __utmb=177965731.3.10.1710821814; __utmt_a2=1; __utmt_b=1; __utmb=81143559.6.10.1710821814; _ga_FL2WFCGS0Y=GS1.1.1710821647.29.1.1710822489.0.0.0; _ga_38RQTHE076=GS1.1.1710821647.29.1.1710822489.0.0.0; __gads=ID=8eb119efaf452d73:T=1709474461:RT=1710822489:S=ALNI_MYydS91k06vzWoYHzeDRrjypAvDRA; __gpi=UID=00000d22d01b2b44:T=1709474461:RT=1710822489:S=ALNI_Ma339b4BWxndbEDhCGn0GMKOwWEsQ; __eoi=ID=0c4c3a2d2799cbd2:T=1709474461:RT=1710822489:S=AA-AfjZ1HMgnt1xZ43IG5c1NhMJm',
    ]

    url = f'http://www.aastocks.com/tc/stocks/market/index/hk-index.aspx'
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
        anchor =soup.findAll('tr',{'class': 'tblM_row firstrow'})
        print(anchor)
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR: {e}')
    if not anchor:
        # stock not found
        return jsonify({
            'error': 2,
        })


    '''return_list.append({
    'news_day': news_day, #return a string of the day of the news, none if no news  
    'news_month': news_month, #return a string of the month of the news, none if no news  
    'news_year' : news_year,#return a string of the year of the news, none if no news  
    'news_url': news_url, #return a string of the url of the news, none if no news  
    'news_title': news_title #return a string of the title of the news, none if no news  
    })
    return jsonify(return_list)'''
    return

# get latest news
# -- parameters --
# stock: stock id (e.g. "9988.hk"/"0008.hk")
# -- return --
# a list of date(string), time(string), url(string), and title(string) of the stock of last 3 days
# if no news, empty list will be returned
# -- error messages --
# 1: cannot connect to server
# 2: stock id not found

# for api test
# localhost:5000/get_news
# {"stock": "9988.hk"}
@app.route('/get_news', methods=['POST'])
def get_news():
    json_data = request.json
    symbol = json_data['stock']
    stock_name = yf_to_aa(symbol)

    if not symbol in STOCK_IDS:
        # stock not found
        return jsonify({
            'error': 2,
        })

    return_list = []
    result = None
    cookie_list = [
        f'mLang=TC; CookiePolicyCheck=0; _ga=GA1.1.1381773272.1710588674; __utma=177965731.1381773272.1710588674.1710588674.1710588674.1; __utmc=177965731; __utmz=177965731.1710588674.1.1.utmcsr=aastocks.com.hk|utmccn=(referral)|utmcmd=referral|utmcct=/; AALTP=1; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; NewChart=Mini_Color=1; AAWS2=; __utmc=81143559; NewsZoomLevel=3; aa_cookie=183.179.122.191_65205_1710592352; __utma=81143559.1381773272.1710588674.1710588712.1710592478.2; __utmz=81143559.1710592478.2.2.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/quote/quick-quote.aspx; __utmt_a3=1; __utmt_a2=1; __utmt_b=1; __utmb=81143559.4.8.1710592478; _ga_FL2WFCGS0Y=GS1.1.1710592538.2.1.1710592539.0.0.0; _ga_38RQTHE076=GS1.1.1710592538.2.1.1710592539.0.0.0; __utmb=177965731.36.9.1710592545018; _ga_MW096YVQH9=GS1.1.1710588675.1.1.1710592545.0.0.0',
    ]

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': random.choice(cookie_list),
        'Host': 'www.aastocks.com',
        'Referer': f'http://www.aastocks.com/tc/stocks/analysis/stock-aafn/{stock_name}/0/hk-stock-news/1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }



    news_time = '9999999999'
    news_id = ''
    stop = False
    datum_date = None
    stop_date = None
    news_url = None
    while not stop:
        url = f'http://www.aastocks.com/tc/resources/datafeed/getmorenews.ashx?cat=hk-stocks-all&newstime={news_time}&newsid={news_id}&period=0&key=&symbol={stock_name}&newsrev=7'
        try:
            result = requests.get(
                url, timeout=40, headers=headers, verify=False
            ).text
            data = json.loads(result)
            if type(data) != list:
                # no data
                break
        except requests.exceptions.ConnectionError as e:
            print(f'ERROR: {e}')
            return jsonify({
                'error': 1,
            })
        for datum in data:
            datum_date = datum.get('dt')[:10].replace('/', '-')
            stop_date = format_date(get_current_date() + datetime.timedelta(days=-2))
            if datum_date >= stop_date:
                news_url = f"http://www.aastocks.com/tc/stocks/analysis/stock-aafn-con/{stock_name}/{datum.get('s')}/{datum.get('id')}/hk-stock-news"
                return_list.append({
                    'url': news_url,
                    'title': datum.get('h'),
                    'date': datum_date,
                    'time': datum.get('dt')[11:]
                })
            else:
                stop = True
                break

        news_time = data[-1].get('dtd')
        news_id = data[-1].get('id')
    return jsonify(return_list)







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
# {"stock": "9988.hk"}
@app.route('/get_future', methods=['POST'])
def get_future():
    json_data = request.json
    symbol = json_data['stock']
    stock_name = yf_to_aa(symbol)
    return_list = []

    stock_pe_ratio = None
    stock_pb_ratio = None

    url = f'http://www.aastocks.com/tc/stocks/analysis/peer.aspx?symbol={stock_name}'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': f'aa_cookie=1.65.150.95_64710_1706931042; MasterSymbol={stock_name}; LatestRTQuotedStocks={stock_name}; _ga=GA1.1.962392854.1706935565; __utma=177965731.962392854.1706935565.1706935566.1706935566.1; __utmc=177965731; __utmz=177965731.1706935566.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_a3=1; __utma=81143559.962392854.1706935565.1706935566.1706935566.1; __utmc=81143559; __utmz=81143559.1706935566.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt_a2=1; __utmt_b=1; CookiePolicyCheck=0; __utmb=177965731.2.10.1706935566; __utmb=81143559.4.10.1706935566; _ga_FL2WFCGS0Y=GS1.1.1706935565.1.1.1706935604.0.0.0; _ga_38RQTHE076=GS1.1.1706935565.1.1.1706935604.0.0.0',
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text

        temp_list = json.loads((result[result.index('tsData')+8:result.index('];', result.index('tsData'))+1]).strip().replace('d0', '"d0"').replace('d1', '"d1"').replace('d2', '"d2"').replace('d3', '"d3"').replace('d4', '"d4"').replace('d5', '"d5"').replace('d6', '"d6"').replace('d7', '"d7"').replace('d8', '"d8"').replace('d9', '"d9"').replace('"d1"0', '"d10"'))
        temp_soup = None
        pe_pb_list=[]
        industry_total = len(temp_list)
        for datum in temp_list:
            temp_soup = BeautifulSoup(datum['d0'], features='html.parser')
            stock_id = temp_soup.find('a').text[:-3]
            pe_ratio = datum['d6']  # 市盈率: can be "N/A"/"無盈利"/"33.06"...
            pb_ratio = datum['d7']  # 市賬率: can be "N/A"/"3.43"...
            if stock_name == stock_id:
                stock_pe_ratio = pe_ratio
                stock_pb_ratio = pb_ratio
            pe_pb_list.append(f'{stock_id}: {pe_ratio} & {pb_ratio}')

    except requests.exceptions.ConnectionError as e:
        print(f'ERROR: {e}')

    url = f'http://www.aastocks.com/tc/stocks/analysis/peer.aspx?symbol={stock_name}&t=6&hk=0'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': f'mLang=TC; _ga=GA1.1.1464946004.1708264002; NewChart=Mini_Color=1; AAWS2=; AAWS=; CookiePolicyCheck=0; __utmc=177965731; AALTP=1; _ga_MW096YVQH9=GS1.1.1709198785.7.0.1709198785.0.0.0; __utmc=81143559; aa_cookie=118.143.134.154_61061_1709196475; __utma=177965731.780197868.1708264002.1709198784.1709202045.11; __utmz=177965731.1709202045.11.5.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; __utma=81143559.1464946004.1708264002.1709198786.1709202045.11; __utmz=81143559.1709202045.11.11.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/tc/stocks/analysis/peer.aspx; MasterSymbol=09988; LatestRTQuotedStocks=00001%3B00004%3B00005%3B02511%3B00776%3B09988; __utmt_a3=1; __utmt_a2=1; __utmt_b=1; __gads=ID=a9c009372c39cc84:T=1708264000:RT=1709204369:S=ALNI_MZAZTfN92pZOHyH9ksQpYursfF0-w; __gpi=UID=00000d09af28c7df:T=1708264000:RT=1709204369:S=ALNI_MYip_3NSn44fhZa_br93obuxL_W1g; __eoi=ID=2b67c1fcdaf92edd:T=1708264000:RT=1709204369:S=AA-AfjYNMLYr5qwpNPB_dHIlFob8; __utmb=177965731.27.10.1709202045; __utmb=81143559.51.10.1709202045; _ga_FL2WFCGS0Y=GS1.1.1709202044.12.1.1709204512.0.0.0; _ga_38RQTHE076=GS1.1.1709202044.12.1.1709204513.0.0.0; cto_bundle=vJmjp19HenJaM3JWanRLQUVLaFdieG1kUEhYNUhhOHo5ZU5NYlpMaXJKSXklMkJoelNPRnBKWVlPUkpCU1J0M3ZGJTJGdFNKMHdMNnpRREF5d1RMWldTYU9yaFQya015NjhtQjUlMkIweFlNUkVSTmFmVmFXWFMyUUlNWFY3NEdKbjJLYTc2ZVAlMkJQME9nZzduVzdrbmJTWW9ISVUyeTlZUSUzRCUzRA',
        'Host': 'www.aastocks.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }
    try:
        result = requests.get(
            url, timeout=40, headers=headers, verify=False
        ).text

        temp_list = json.loads((result[result.index('tsData')+8:result.index('];', result.index('tsData'))+1]).strip().replace('d0', '"d0"').replace('d1', '"d1"').replace('d2', '"d2"').replace('d3', '"d3"').replace('d4', '"d4"').replace('d5', '"d5"').replace('d6', '"d6"').replace('d7', '"d7"').replace('d8', '"d8"').replace('d9', '"d9"').replace('"d1"0', '"d10"'))
        temp_soup = None
        ARG_list=[]
        stock_ARG=None
        for datum in temp_list:
            temp_soup = BeautifulSoup(datum['d0'], features='html.parser')
            stock_id = temp_soup.find('a').text[:-3]
            ARG = datum['d3']  # 年度收入增長: can be "+"/"N/A"/"-"...
            if f'{stock_id}'==f'{stock_name}':
                stock_ARG=ARG
            ARG_list.append(f'{stock_id}: {ARG}')
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR: {e}')
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




        #finding the revenue of the stock
        soup = BeautifulSoup(result, features='html.parser')
        anchor =soup.select('td.cfvalue.txt_r.cls.bold')
        if(anchor[0].text.strip()=="N/A" and "-"):
            last_year_revenue = "N/A"
            two_year_revenue = "N/A"
            three_year_revenue = "N/A"
        else:
            last_year_revenue = anchor[0].text.strip()
            if(anchor[0].previous_sibling.previous_sibling.text.strip()=="盈利(百萬)" and "-"):
        
                two_year_revenue = "N/A"
                three_year_revenue = "N/A"
            else:
                two_year_revenue =anchor[0].previous_sibling.previous_sibling.text.strip()
                if(anchor[0].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()=="盈利(百萬)" and "-"):
                    three_year_revenue = "N/A"
                else:
                    three_year_revenue = anchor[0].previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()
        '''if(last_year_revenue[0]=='-'):
            last_year_revenue=last_year_revenue[1:]
            last_year_revenue=float(last_year_revenue)*(-1)
        if(last_year_revenue[0]=='-'):
            two_year_revenue=two_year_revenue[1:]
            two_year_revenue=float(two_year_revenue)*(-1)
        if(three_year_revenue[0]=='-'):
            three_year_revenue=three_year_revenue[1:]
            three_year_revenue=float(three_year_revenue)*(-1)'''
        print(last_year_revenue)
        print(two_year_revenue)
        print(three_year_revenue)
        if(last_year_revenue !="N/A" and two_year_revenue !="N/A" and three_year_revenue !="N/A" ):
            last_year_revenue=float(last_year_revenue.replace(',', ''))
            two_year_revenue=float(two_year_revenue.replace(',', ''))
            three_year_revenue=float(three_year_revenue.replace(',', ''))
            if(last_year_revenue>two_year_revenue and two_year_revenue>three_year_revenue):
                revenue_growth=1 #(increasing)
            if(last_year_revenue<=two_year_revenue and two_year_revenue>=three_year_revenue and last_year_revenue>=three_year_revenue):
                revenue_growth=2 #(overall increasing)
            if(last_year_revenue>=two_year_revenue and two_year_revenue<=three_year_revenue and last_year_revenue>=three_year_revenue):
                revenue_growth=2 #(overall increasing)
            if(last_year_revenue<=two_year_revenue and two_year_revenue>=three_year_revenue and last_year_revenue<=three_year_revenue):
                revenue_growth=3 #(average)
            if(last_year_revenue>=two_year_revenue and two_year_revenue<=three_year_revenue and three_year_revenue>=last_year_revenue):
                revenue_growth=4 #(overall decreasing) 
            if(last_year_revenue<two_year_revenue and two_year_revenue<three_year_revenue):
                revenue_growth=5 #(decreasing)
        if(last_year_revenue =="N/A" or two_year_revenue =="N/A" or three_year_revenue =="N/A" ):
            revenue_growth=None
        print('revenue overall:')
        print(revenue_growth)
        '''
        1 2 3 --> 1 increasing
        1 3 2 --> 2 overall increasing
        2 1 3 --> 2 overall increasing
        2 3 1 --> 3 average 
        3 1 2 --> 4 overall decreasing 
        3 2 1 --> 5 decreasing
        '''

        #finding the %revenue of the stock last year
        soup = BeautifulSoup(result, features='html.parser')
        anchor =soup.select('td.cfvalue.txt_r.cls.bold')
        if(anchor[1].text.strip()!="-"):
            last_year_revenue_percent = float(anchor[1].text.strip())
        else:
            last_year_revenue_percent=(float(last_year_revenue.replace(',', ''))-float(two_year_revenue.replace(',', '')))/float(two_year_revenue.replace(',', ''))
            last_year_revenue_percent=last_year_revenue_percent*100
            last_year_revenue_percent=round(last_year_revenue_percent, 2)
        print(last_year_revenue_percent)
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

        if(last_year_EPS !="N/A" and two_year_EPS !="N/A" and three_year_EPS !="N/A"):
            last_year_EPS=float(last_year_EPS)
            two_year_EPS=float(two_year_EPS)
            three_year_EPS=float(three_year_EPS)
            if(last_year_EPS>two_year_EPS and two_year_EPS>three_year_EPS):
                EPS_growth=1 #(increasing)
            if(last_year_EPS<=two_year_EPS and two_year_EPS>=three_year_EPS and last_year_EPS>=three_year_EPS):
                EPS_growth=2 #(overall increasing)
            if(last_year_EPS>=two_year_EPS and two_year_EPS<=three_year_EPS and last_year_EPS>=three_year_EPS):
                EPS_growth=2 #(overall increasing)
            if(last_year_EPS<=two_year_EPS and two_year_EPS>=three_year_EPS and last_year_EPS<= three_year_EPS):
                EPS_growth=3 #(average)
            if(last_year_EPS>=two_year_EPS and two_year_EPS<=three_year_EPS and three_year_EPS>=last_year_EPS):
                EPS_growth=4 #(overall decreasing) 
            if(last_year_EPS<two_year_EPS and two_year_EPS<three_year_EPS):
                EPS_growth=5 #(decreasing)
        if(last_year_EPS =="N/A" or two_year_EPS =="N/A" or three_year_EPS =="N/A" ):
            EPS_growth=None
        print('EPS overall:')
        print(EPS_growth)
        '''
        1 2 3 --> 1 increasing
        1 3 2 --> 2 overall increasing
        2 1 3 --> 2 overall increasing
        2 3 1 --> 3 average 
        3 1 2 --> 4 overall decreasing 
        3 2 1 --> 5 decreasing
        '''


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

        #finding category name
        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('div',{'class': 'tabPanel_Title'})
        categories_name=anchor.text.strip()
        #finding annual revenue growth (年度收入增長)
        annual_revenue_growth_list=[]
        for data in ARG_list:
            annual_revenue_growth_list.append(data.split(":")[1].strip())
        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('table',{'id': 'tblTS2'})
        x=anchor.find_all('td',{'class':'txt_r'})
        if not anchor:
            # stock not found
            return jsonify({
                'error': 2,
            })
        i=0
        while i+1< len(x):
            while i%10==2:
                annual_revenue_growth_list.append(x[i].text)
                i = i + 1
            i = i + 1
        temp_ARG_list=[]
        for ARG in annual_revenue_growth_list:
            if  ARG=="N/A":
                pass
            else:
                temp_ARG_list.append(float(ARG.replace(',', '').strip().strip("%"))/100)
        
        #check if ARG is None and assign the correct ARG to it
        if(stock_ARG==None):
            soup = BeautifulSoup(result, features='html.parser')
            anchor = soup.find('a',{'title': f'{stock_name}'+".HK"})
            print(anchor)
            stock_ARG=anchor.parent.parent.parent.find_next_sibling().find_next_sibling().find_next_sibling().text.strip()
            
        print(stock_ARG)
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

    # find pe and pb ratio in same categories
        pe_ratio_list=[]
        pb_ratio_list=[]
        for data in pe_pb_list:
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
                industry_total += 1
                i = i + 1
            i = i + 1
        
        temp_pe_ratio_list = []
        for pe_ratio in pe_ratio_list:
            if pe_ratio=="無盈利"or pe_ratio== "N/A":
                temp_pe_ratio_list.append(99999)
            else:
                temp_pe_ratio_list.append(float(pe_ratio.strip()))
        temp_pb_ratio_list = []
        for pb_ratio in pb_ratio_list:
            if  pb_ratio=="N/A":
                pass
            else:
                temp_pb_ratio_list.append(float(pb_ratio.strip()))

        soup = BeautifulSoup(result, features='html.parser')
        anchor = soup.find('span',{'class': 'PEAvgShort'})
        average_pe_ratio=anchor.parent.find_next_sibling().text.strip()



        # find pe ratio and pb ratio of current stock
        trs = soup.find('table', {'id': 'tblTS2'}).find('tbody').find_all('tr')
        for tr in trs:
            if stock_name == tr.find('td', {'class': 'nls'}).find('a').text.strip()[:-3]:
                tds = tr.find_all('td')
                stock_pe_ratio = tds[6].text.strip()
                stock_pb_ratio = tds[7].text.strip()




        # find pe ratio rank and number of class in same categories
        if(stock_pe_ratio=='N/A'):
            pe_ratio_categories=None
            average_pe_ratio=None
            pe_ratio_rank=None
            total_number_pe_ratio=None
            stock_pe_ratio=None
        elif(stock_pe_ratio=='無盈利'):
            pe_ratio_categories='無盈利'
            average_pe_ratio=None
            pe_ratio_rank=None
            total_number_pe_ratio=None
        else:
            stock_pe_ratio = float(stock_pe_ratio)
            target_number = float(stock_pe_ratio)
            sorted_pe_ratio_list = sorted(temp_pe_ratio_list) 
            # Sort the list in ascending order
            pe_ratio_rank = sorted_pe_ratio_list.index(target_number) +1  # minus 1 to get the rank (1-based indexing)
            print(pe_ratio_rank)     
            print(len(sorted_pe_ratio_list))
            print(stock_pe_ratio)
            total_number_pe_ratio=len(sorted_pe_ratio_list)
            average_pe_ratio=float(average_pe_ratio)
            average_pe_ratio=round(average_pe_ratio,2)
            if(target_number>average_pe_ratio):
                pe_ratio_categories=1 # 市盈率超過行業平均值
            if(average_pe_ratio==target_number):
                pe_ratio_categories=2 # 市盈率等於行業平均值
            if(target_number<average_pe_ratio):
                pe_ratio_categories=3 # 市盈率低於行業平均值
            print(pe_ratio_categories)
            print("----------------")  


        # find pb ratio rank and number of class in same categories
        if(stock_pb_ratio=='N/A'):
            pb_ratio_categories=None
            average_pb_ratio=None
            pb_ratio_rank=None
            total_number_pb_ratio=None
            stock_pb_ratio=None
        elif(stock_pb_ratio=='無盈利'):
            pb_ratio_categories='無盈利'
            average_pb_ratio=None
            pb_ratio_rank=None
            total_number_pb_ratio=None
        else:
            stock_pb_ratio = float(stock_pb_ratio)
            target_number = float(stock_pb_ratio)
            sorted_pb_ratio_list = sorted(temp_pb_ratio_list)  # Sort the list in ascending order
            pb_ratio_rank = sorted_pb_ratio_list.index(target_number) +1  # minus 1 to get the rank (1-based indexing)
            print(pb_ratio_rank)     
            print(len(temp_pb_ratio_list))
            total_pb_ratio=0
            for pb_ratio in sorted_pb_ratio_list:
                total_pb_ratio=total_pb_ratio+pb_ratio
            average_pb_ratio=float(total_pb_ratio/len(temp_pb_ratio_list))
            average_pb_ratio=round(average_pb_ratio,2)
            total_number_pb_ratio=len(sorted_pb_ratio_list)
            if(target_number>average_pb_ratio):
                pb_ratio_categories=1 # 市賬率超過行業平均值
            if(target_number==average_pb_ratio):
                pb_ratio_categories=2 # 市賬率等於行業平均值
            if(target_number<average_pb_ratio):
                pb_ratio_categories=3 # 市賬率低於行業平均值
            print(pb_ratio_categories)
            print("----------------")



        # find annual revenue growth (年度收入增長) of class in same categories
        print(stock_ARG)
        if(stock_ARG!='N/A'):
            target_number = float(stock_ARG.strip().strip("%"))/100 
            sorted_ARG_list = sorted(temp_ARG_list,reverse=True) 
            ARG_rank = sorted_ARG_list.index(target_number) +1  # minus 1 to get the rank (1-based indexing)
            print(ARG_rank)     
            print(len(sorted_ARG_list))
            total_number_ARG=len(sorted_ARG_list)
            total_ARG=0
            for ARG in sorted_ARG_list:
                total_ARG=total_ARG+ARG
            average_ARG=total_ARG/len(sorted_ARG_list)
            average_ARG=round(average_ARG,2)
            if(target_number>average_ARG):
                ARG_categories=1 # 年度收入增長超過行業平均值
            if(target_number==average_ARG):
                ARG_categories=2 # 年度收入增長等於行業平均值
            if(target_number<average_ARG):
                ARG_categories=3 # 年度收入增長低於行業平均值
            print(ARG_categories)
        else:
            ARG_rank=None
            ARG_categories=None
            total_number_ARG=None
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })

    return_list=[]
    return_list.append({
        'categories_name': categories_name, #return a string, categories name
        'EPS_growth': EPS_growth, #return a integer(1-5) or'N/A', 1 increasing ,2 overall increasing,3 average,4 overall decreasing,5 decreasing, will be 'N/A' if one of the revenue in la
        'revenue_growth_percentage': last_year_revenue_percent, #return a float, ARG percentage  without % sign
        'pe_ratio_categories': pe_ratio_categories, #return a integer(1-3), 'None' or '無盈利' 1 市盈率超過行業平均值, 2 市盈率等於行業平均值 ,3 市盈率低於行業平均值 , if pe ratio of that stock is "N/A" or '無盈利', this will change to itcorrespondingly
        'average_pe_ratio': average_pe_ratio, # return a float ,'None', average pe ratio of the category, if pe_ratio_categories is "None" or '無盈利', this will be 'None' too
        'pe_ratio_rank': pe_ratio_rank, # return a integer or 'None', rank of the pe ratio in the category ,if pe_ratio_categories is "None" or '無盈利', this will be 'None' too
        'total_number_pe_ratio': total_number_pe_ratio, # return a integer or 'None', total number of pe ratio in the category,if pe_ratio_categories is "None" or '無盈利', this will be 'None' too
        'stock_pe_ratio': stock_pe_ratio, # float or '無盈利' or None
        'pb_ratio_categories': pb_ratio_categories, # return a float, average pb ratio of the category
        'average_pb_ratio': average_pb_ratio, #return a integer(1-3), 'None' or '無盈利' 1 市賬率超過行業平均值, 2 市賬率等於行業平均值 ,3 市賬率低於行業平均值 , if pb ratio of that stock is "N/A" or '無盈利', this will change to itcorrespondingly
        'pb_ratio_rank': pb_ratio_rank, # return a integer or 'None', rank of the pb ratio in the category ,if pb_ratio_categories is "None" or '無盈利', this will be 'None' too
        'total_number_pb_ratio': total_number_pb_ratio, # return a integer or 'None', total number of pb ratio in the category,if pb_ratio_categories is "None" or '無盈利', this will be 'None' too
        'stock_pb_ratio': stock_pb_ratio, # float or '無盈利' or None
        'revenue_growth': revenue_growth, #return a integer(1-5) or None, 1 increasing ,2 overall increasing,3 average,4 overall decreasing,5 decreasing, will be 'N/A' if one of the revenue in last three years is 'N/A'
        'annual_revenue_growth_rank': ARG_rank, # return a integer or 'None', rank of the ARG in the category , if ARG is 'N/A', this become 'None'
        'total_number_annual_revenue_growth': total_number_ARG, # return a integer or 'None', rank of the ARG in the category , if ARG is 'N/A', this become 'None'
        'industry_total': industry_total,
    })
    return jsonify(return_list)










#debug (if here stop, server will hang)
# print(yf_to_aa('9988.hk'))
