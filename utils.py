# convert from:
# '9988.hk' to '09988'
# '0001.hk' to '00001'
def yf_to_aa(key):
    key = key[:-3]
    while len(key) < 5:
        key = '0' + key
    return key