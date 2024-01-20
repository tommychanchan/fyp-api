ready = False
apis = {}
db_client = None
fyp_db = None
qa_col = None
ta_fa_col = None

def init():
    import pymongo

    global db_client, fyp_db, qa_col, ta_fa_col

    with open('tokens.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines()]
        apis['nasdaq'] = lines[0]

    # connect to database
    db_client = pymongo.MongoClient('localhost', 27017)
    fyp_db = db_client['fyp']
    qa_col = fyp_db['qa']
    ta_fa_col = fyp_db['ta_fa']

    ready = True


if not ready:
    init()
