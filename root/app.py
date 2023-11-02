import json
import random
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
                
                prev_close_price, open_price = (float(x.strip()) for x in soup.find('div', {'id': 'valPrevClose'}).text.split('/'))
                
                day_low, day_high = (float(x.strip()) for x in soup.find('div', {'id': 'valRange'}).text.split('-'))
                
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

                avg_price = float(soup.find('div', string='均價').parent.find('div', {'class': 'float_r'}).text.strip())

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

                turnover_rate = float(soup.find('div', {'data-key': 'Turnover Rate'}).parent.parent.parent.find('div', {'class': 'float_r'}).text.strip().strip('%')) / 100

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

#debug (if here stop, server will hang)
# print(yf_to_aa('9988.hk'))
