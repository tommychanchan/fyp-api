import requests
import json


apis = {}

with open('tokens.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    apis['nasdaq'] = lines[0]

import nasdaqdatalink
nasdaqdatalink.ApiConfig.api_key = apis['nasdaq']
data = nasdaqdatalink.get('HKEX/00607')
data['Close'] = data['Previous Close'].shift(-1)
data.dropna(subset = ['Close'], inplace=True)
data['Adj Close'] = data['Close']
url = 'http://localhost:5000/stock_split'
headers = {}
payload = {'stock': '0607.hk'}
try:
    result = requests.post(
        url, timeout=40, headers=headers, json=payload, verify=False
    ).text

    split_dividend_list = sorted(json.loads(result), key=lambda d: d['date'], reverse=True)
    for datum in split_dividend_list:
        if len(data.loc[:datum['date']]) > 0 and datum['splitDividend'] == 'split':
            data.loc[:datum['date'], 'Adj Close'] *= datum['rate']
            data.drop(data.loc[:datum['date']].index[-1], inplace=True)
    data.iloc[-20:].to_csv('test.csv', sep=',', encoding='utf-8')
except requests.exceptions.ConnectionError as e:
    print(f'ERROR({payload}): {e}')

