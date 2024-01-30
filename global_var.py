ready = False
tokens = {}
db_client = None
fyp_db = None
qa_col = None
ta_fa_col = None
users_col = None
rasa_ip = None

def init():
    import pymongo
    import json

    global db_client, fyp_db, qa_col, ta_fa_col, users_col
    global rasa_ip

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

    ready = True


if not ready:
    init()
