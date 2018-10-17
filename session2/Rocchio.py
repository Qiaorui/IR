from __future__ import print_function
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import argparse
import numpy as np
import re
from collections import defaultdict

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q
from TFIDFViewer import normalize, doc_count, document_term_vector


def search(client, query, k, index=None):
    s = Search(using=client, index=index)

    if query is not None:
        q = Q('query_string', query=query[0])
        for i in range(1, len(query)):
            q &= Q('query_string', query=query[i])

        s = s.query(q)
        response = s[0:k].execute()
        return response

    else:
        print('No query parameters passed')


# Parse a query and extract the word and weight into 2 list
def parse_query(query):
    q = []
    w = []
    for s in query:
        m = re.match(r'(\w+)\^?([\d.]+)?', s)
        q.append(m.group(1))
        w.append(1.0 if m.group(2) is None else float(m.group(2)))
    return q, w


def toTFIDF(client, index, file_id):

    # Get document terms frequency and overall terms document frequency
    file_tv, file_df = document_term_vector(client, index, file_id)

    max_freq = max([f for _, f in file_tv])

    dcount = doc_count(client, index)

    tfidfw = []
    for (t, w),(_, df) in zip(file_tv, file_df):
        # tfidf = fdi/max fd  * log2 D/df
        tdidf = w/max_freq * np.log2(dcount/df)
        # Only store non zero weight terms to optimize the computation
        if tdidf > 0:
            tfidfw.append((t, tdidf))

    return tfidfw


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', default=None, required=True, help='Index to search')
    parser.add_argument('--k', default=10, type=int, help='Number of relevant documents to return')
    # **************************************************************************************************************
    # Roccio parameters
    parser.add_argument('--nrounds', default=5, type=int, help='Number of applications of Rocchio’s rule')
    parser.add_argument('--R', default=100, type=int, help='Maximum number of terms to be kept in the new query')
    parser.add_argument('--alpha', default=1, type=float, help='Weight in the Rocchio rule for original query')
    parser.add_argument('--beta', default=1, type=float, help='Weight in the Rocchio rule for relevant document')
    # **************************************************************************************************************
    parser.add_argument('--query', default=None, nargs=argparse.REMAINDER, help='List of words to search')

    args = parser.parse_args()

    index = args.index
    query = args.query
    k = args.k
    nrounds = args.nrounds
    R = args.R
    alpha = args.alpha
    beta = args.beta

    print("Receive query", query)
    q, w = parse_query(query)
    docs = None
    try:
        client = Elasticsearch()
        for ite in range(nrounds):
            print("******************************************************")
            print("iteration", ite + 1)
            print("Term vector :", q)
            print("Weight vector :", w)
            query = [term + "^" + str(weight) for term, weight in zip(q, w)]
            print("Composed query :", query)
            # Find all relevant documents
            docs = search(client, query, k, index)

            # For each document, compute the tf idf and pruning the list. Finally store into a dictionary
            d = defaultdict(float)
            for doc in docs:
                tfidf = toTFIDF(client, index, doc.meta.id)
                # Pruning the list
                tfidf.sort(key=lambda tup: tup[1])
                tfidf = tfidf[-R:]
                # After pruning, normalize. Then we can get larger weight.
                tfidf = normalize(tfidf)
                # Sum of tfidf, a way to accelerate the process
                for t, weight in tfidf:
                    d[t] += weight

            # Then we compute new query by apply Rocchio rule
            new_w = []
            for term, weight in zip(q, w):
                new_w.append(weight * alpha + beta * d[term] / k)
            # Update new w
            w = new_w

    except NotFoundError:
        print('Index %s does not exists' % index)

    print("******************************************************")
    for r in docs:  # only returns a specific number of results
        print('ID= %s SCORE=%s' % (r.meta.id, r.meta.score))
        print('PATH= %s' % r.path)
        print('-----------------------------------------------------------------')
