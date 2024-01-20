import json
from bson import json_util
import datetime

def parse_json(data):
    return json.loads(json_util.dumps(data))

def get_current_datetime():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

def get_current_date():
    return datetime.datetime.combine(get_current_datetime(), datetime.time.min)


# convert from:
# '9988.hk' to '09988'
# '0001.hk' to '00001'
def yf_to_aa(key):
    key = key[:-3]
    while len(key) < 5:
        key = '0' + key
    return key

def float_or_none(s):
    try:
        return float(s)
    except:
        return None

def remove_unit(num, unit):
    # num must be number
    if unit == '兆' or unit == '萬億':
        num *= 1000000000000
    elif unit == '千億':
        num *= 100000000000
    elif unit == '百億':
        num *= 10000000000
    elif unit == '十億':
        num *= 1000000000
    elif unit == '億':
        num *= 100000000
    elif unit == '千萬':
        num *= 10000000
    elif unit == '百萬':
        num *= 1000000
    elif unit == '十萬':
        num *= 100000
    elif unit == '萬':
        num *= 10000
    elif unit == '千':
        num *= 1000
    elif unit == '百':
        num *= 100
    elif unit == '十':
        num *= 10
    return num

def extract_num_unit(s):
    # s is sth like '17,469.89億'
    count = 0
    for c in s:
        if c in '0123456789,.':
            count += 1
        else:
            break

    return float(s[:count].replace(',', '')), s[count:]
