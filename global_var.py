ready = False
apis = {}

def init():
    with open('tokens.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines()]
        apis['nasdaq'] = lines[0]
    ready = True


if not ready:
    init()
