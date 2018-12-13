from pymongo import MongoClient
from bson.code import Code

mapper = Code("""
function() {
    for (var i = 0; i < this.items.length; i++) {
        emit(this.items[i],1);
        for (var j = i + 1; j < this.items.length; j++) {
            if (this.items[i] < this.items[j]) {
                emit({word1: this.items[i], word2: this.items[j]}, 1);
            } else {
                emit({word1: this.items[j], word2: this.items[i]}, 1);
            }
        }
    }
}
""")

reducer = Code("""
function(key,values) {
    var total = 0;
    for (var i = 0; i < values.length; i++) {
        total += values[i];
    }
        return total;
}
""")


def read(path):
    with open(path) as f:
        for line in f:
            d = {'items': line.strip().split(',')}
            db.market.insert(d)


if __name__ == '__main__':

    print("**************** Connect to Mongo ****************")
    client = MongoClient()
    db = client.ir

    try:

        if "market" in db.list_collection_names():
            db.market.remove()
        if "counts" in db.list_collection_names():
            db.counts.remove()
        if "rules" in db.list_collection_names():
            db.rules.remove()

        print("****************** Reading Data ******************")
        read("groceries.csv")
        print(db.market.count(), "documents have been inserted")

        print("******************* Map Reduce *******************")
        r = db.market.map_reduce(mapper, reducer, "counts")
        print(r.count(), "counted items have been inserted")

        print("********* Compute support and confidence *********")

        # Read map reduce results and store into python structure
        items = {}
        pairs = {}
        for doc in db.counts.find():
            if isinstance(doc['_id'], str):
                items[doc['_id']] = doc['value']
            else:
                pairs[(doc['_id']['word1'], doc['_id']['word2'])] = doc['value']

        print(len(items), "unique items found")

        # Compute association rule
        sup = {}
        conf = {}
        N = db.market.count()
        for (a, b), value in pairs.items():
            sup[a, b] = sup[b, a] = value / N
            conf[a, b] = value / items[a]
            conf[b, a] = value / items[b]

        # Write the computed association rules into mongo
        for comb in sup.keys():
            rule = {"rule": {"if": comb[0], "then": comb[1]}, "confidence": conf[comb], "support": sup[comb]}
            db.rules.insert(rule)

        print(db.rules.count(), "rules have been inserted")

    except Exception as e:
        print("Exception:", e)
        print("Self-destroying...")
        db.command("dropDatabase")
