from pymongo import MongoClient
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', default=0.01, type=float, help='Support threshold')
    parser.add_argument('-c', default=0.01, type=float, help='Confidence threshold')
    args = parser.parse_args()
    s = args.s
    c = args.c

    client = MongoClient()
    db = client.ir
    items = {}
    pairs = {}
    for doc in db.counts.find():
        if isinstance(doc['_id'], str):
            items[doc['_id']] = doc['value']
        else:
            pairs[(doc['_id']['word1'], doc['_id']['word2'])] = doc['value']

    print("items: ", len(items))
    print("pairs: ", len(pairs))

    sup = {}
    conf = {}
    N = db.market.count()
    for key, value in pairs.items():
        sup[key] = value / N
        conf[key[0], key[1]] = value / items[key[0]]
        conf[key[1], key[0]] = value / items[key[1]]

    filtered_rules = [rule for rule in sup.keys() if sup[rule] > s and conf[rule] > c]
    for r in filtered_rules:
        print(r)
    print("Number of association rules ", len(filtered_rules))
