from __future__ import print_function
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
import argparse
import os
import codecs
from elasticsearch_dsl import Index, analyzer, tokenizer
import numpy as np
import re
from collections import defaultdict
from elasticsearch.client import CatClient

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q



def search(client, q, k, index=None):
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


def document_term_vector(client, id, index):
    """
    Returns the term vector of a document and its statistics a two sorted list of pairs (word, count)
    The first one is the frequency of the term in the document, the second one is the number of documents
    that contain the term

    :param client:
    :param index:
    :param id:
    :return:
    """
    termvector = client.termvectors(index=index, doc_type='document', id=id, fields=['text'],
                                    positions=False, term_statistics=True)

    file_td = {}
    file_df = {}

    if 'text' in termvector['term_vectors']:
        for t in termvector['term_vectors']['text']['terms']:
            file_td[t] = termvector['term_vectors']['text']['terms'][t]['term_freq']
            file_df[t] = termvector['term_vectors']['text']['terms'][t]['doc_freq']
    return sorted(file_td.items()), sorted(file_df.items())


# Parse a query and extract the word and weight into 2 list
def parse_query(query):
    q = []
    w = []
    for s in query:
        m = re.match(r'(\w+)\^?([\d.]+)?', s)
        q.append(m.group(1))
        w.append(1.0 if m.group(2) is None else float(m.group(2)))
    return q, w



def normalize(tw):
    """
    Normalizes the weights in t so that they form a unit-length vector
    It is assumed that not all weights are 0
    :param tw:
    :return:
    """
    norm = np.sqrt(sum([x*x for _, x in tw]))
    return [(t, w/norm) for t, w in tw]



def doc_count(client, index):
    """
    Returns the number of documents in an index

    :param client:
    :param index:
    :return:
    """
    return int(CatClient(client).count(index=[index], format='json')[0]['count'])


def toTFIDF(client, index, file_id):
    """
    Returns the term weights of a document

    :param file:
    :return:
    """

    # Get document terms frequency and overall terms document frequency
    file_tv, file_df = document_term_vector(client, file_id, index)

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
                tfidf.sort(key= lambda tup: tup[1])
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


