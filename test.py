import requests
import json
from bs4 import BeautifulSoup

from global_var import *





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
    print('Length:', len(temp_list))
    temp_soup = None
    pe_pb_list=[]
    for datum in temp_list:
        temp_soup = BeautifulSoup(datum['d0'], features='html.parser')
        stock_id = temp_soup.find('a').text[:-3]
        pe_ratio = datum['d6']  # 市盈率: can be "N/A"/"無盈利"/"33.06"...
        pb_ratio = datum['d7']  # 市賬率: can be "N/A"/"3.43"...
        pe_pb.append(f'{stock_id}: {pe_ratio} & {pb_ratio}')
except requests.exceptions.ConnectionError as e:
    print(f'ERROR: {e}')

    url = f'http://www.aastocks.com/tc/stocks/analysis/peer.aspx?symbol={stock_name}&t=1&hk=0'
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
    print('Length:', len(temp_list))
    temp_soup = None
    annual_revenue_growth_list=[]
    for datum in temp_list:
        temp_soup = BeautifulSoup(datum['d0'], features='html.parser')
        stock_id = temp_soup.find('a').text[:-3]
        annual_revenue_growth = datum['d3']  # 年度收入增長: can be "N/A"/"無盈利"/"33.06"...
        annual_revenue_growth.append(f'{stock_id}: {annual_revenue_growth}')
except requests.exceptions.ConnectionError as e:
    print(f'ERROR: {e}')
