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
        payload = {'stock': yf}
        try:
            result = requests.post(
                url, timeout=40, headers=headers, json=payload, verify=False
            ).text

            result_json = json.loads(result)
            if type(result_json) != list and result_json.get('error'):
                if result_json.get('error') == 2:
                    return_list.append({
                        'symbol': yf,
                        'error': 3,
                    })
                    continue

            split_dividend_list = sorted(result_json, key=lambda d: d['date'], reverse=True)
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
# portfolio: an object of the buying stock information
# -- return --
# an object with error number
# -- error messages --
# 0: no error

# for api test
# localhost:5000/save_portfolio
# {"userID": "Sender", "date": "2000/01/01", "price": 62.53, "stock": "9988.hk", "stock_number": 100}
@app.route('/save_portfolio', methods=['POST'])
def save_portfolio():
    json_data = request.json
    user_id = json_data['userID']
    date = json_data['date']
    price = json_data['price']
    stock = json_data['stock']
    stock_number = json_data['stock_number']

    error = 0

    portfolio_col.insert_one({
        'userID': user_id,
        'date': date,
        'price': price,
        'stock': stock,
        'stock_number': stock_number,
    })

    return jsonify({
        'error': error,
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
# stock: stock id (e.g. "9988.hk"/"0008.hk")
# -- return --
# a list of stock split/dividend info
# -- error messages --
# 1: cannot connect to server
# 2: stock id not found

# for api test
# localhost:5000/stock_split
# {"stock": "0607.hk"}
@app.route('/stock_split', methods=['POST'])
def stock_split():
    json_data = request.json
    symbol = json_data['stock']
    stock_name = yf_to_aa(symbol)


    return_list = []

    cookie_list = [
        'aa_cookie=1.65.201.178_57487_1703743573; mLang=TC; CookiePolicyCheck=0; __utma=177965731.1037720175.1703741287.1703741287.1703741287.1; __utmc=177965731; __utmz=177965731.1703741287.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmt_a3=1; _ga=GA1.1.886609921.1703741287; _ga_MW096YVQH9=GS1.1.1703741302.1.0.1703741302.0.0.0; AALTP=1; MasterSymbol=00607; LatestRTQuotedStocks=00607; NewChart=Mini_Color=1; AAWS2=; __utma=81143559.886609921.1703741287.1703741304.1703741304.1; __utmc=81143559; __utmz=81143559.1703741304.1.1.utmcsr=aastocks.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt_a2=1; __utmt_b=1; _ga_FL2WFCGS0Y=GS1.1.1703741286.1.1.1703741411.0.0.0; _ga_38RQTHE076=GS1.1.1703741286.1.1.1703741412.0.0.0; __utmb=177965731.18.10.1703741287; __utmb=81143559.10.9.1703741366373',
    ]

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
            return jsonify({
                'error': 2,
            })

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
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR({symbol}): {e}')
        return jsonify({
            'error': 1,
        })


    return jsonify(return_list)






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


    return parse_json(to_return)









#debug (if here stop, server will hang)
# print(yf_to_aa('9988.hk'))
