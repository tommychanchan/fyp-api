apis = {}

with open('tokens.txt') as f:
    lines = [line.strip() for line in f.readlines()]
    apis['nasdaq'] = lines[0]

import nasdaqdatalink
nasdaqdatalink.ApiConfig.api_key = apis['nasdaq']
data = nasdaqdatalink.get('HKEX/09988')
print(data)
