import pymongo
import json

tokens = {}

with open('tokens.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    tokens['nasdaq'] = lines[0]

with open('ips.json', 'r') as f:
    ips_json = json.load(f)
    rasa_ip = ips_json['flaskToRasa']
    mongo_host = ips_json['flaskToMongo']['host']
    mongo_port = ips_json['flaskToMongo']['port']

# connect to database
db_client = pymongo.MongoClient(mongo_host, mongo_port)
fyp_db = db_client['fyp']
qa_col = fyp_db['qa']
ta_col = fyp_db['ta']
users_col = fyp_db['users']
portfolio_col = fyp_db['portfolio']
split_col = fyp_db['split']
real_time_col = fyp_db['real_time']
