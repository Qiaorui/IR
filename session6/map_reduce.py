from pymongo import MongoClient
from bson.code import Code

mapper = Code("""
function() {
    for (var i = 0; i < this.items.length; i++) {
        emit(this.items[i],1);

        for (var j = i + 1; j < this.items.length; j++) {
            if (this.items[i] < this.items[j]) {
                emit({word1: this.items[i], word2: this.items[j]}, 1);
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
        if "market" in db.collections_names():
            db.market.remove()
        if "counts" in db.collections_names():
            db.counts.remove()

        print("****************** Reading Data ******************")
        read("groceries.csv")
        print(db.market.count(), "documents have been inserted")

        print("******************* Map Reduce *******************")
        r = db.market.map_reduce(mapper, reducer, "counts")
        print("finished reducing")
        print(r.count(), "documents have been inserted")
    except Exception as e:
        print("Exception:", e)
        print("Self-destroying...")
        db.command("dropDatabase")
