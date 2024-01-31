import pymongo
import json

tokens = {}

with open('tokens.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    tokens['nasdaq'] = lines[0]

with open('ips.json', 'r') as f:
    ips_json = json.load(f)
    rasa_ip = ips_json['flaskToRasa']

# connect to database
db_client = pymongo.MongoClient('localhost', 27017)
fyp_db = db_client['fyp']
qa_col = fyp_db['qa']
ta_fa_col = fyp_db['ta_fa']
users_col = fyp_db['users']
