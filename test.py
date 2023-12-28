apis = {}

with open('tokens.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    apis['nasdaq'] = lines[0]

import nasdaqdatalink
nasdaqdatalink.ApiConfig.api_key = apis['nasdaq']
data = nasdaqdatalink.get('HKEX/00607')
data['Close'] = data['Previous Close'].shift(-1)
data.iloc[-20:].to_csv('test.csv', sep=',', encoding='utf-8')
