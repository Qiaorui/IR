from __future__ import print_function
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
import argparse
import os
import codecs
from elasticsearch_dsl import Index, analyzer, tokenizer
import glob
import numpy as np
import re
from collections import defaultdict

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


def document_term_vector(client, id, index=None):
    """
    Returns the term vector of a document and its statistics a two sorted list of pairs (word, count)
    The first one is the frequency of the term in the document

    :param client:
    :param index:
    :param id:
    :return:
    """
    termvector = client.termvectors(index=index, doc_type='document', id=id, fields=['text'],
                                    positions=False, term_statistics=True)

    file_td = {}

    if 'text' in termvector['term_vectors']:
        for t in termvector['term_vectors']['text']['terms']:
            file_td[t] = termvector['term_vectors']['text']['terms'][t]['term_freq']
    return sorted(file_td.items())


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


def toTFIDF(fd, df, R):
    """
    Returns the term weights of a document

    :param file:
    :return:
    """

    tfidf_matrix = []
    dcount = len(fd)

    for doc in fd:
        max_freq = max([f for _, f in doc])

        tfidfw = []
        for t, w in doc:
            # tfidf = fdi/max fd  * log2 D/df
            tdidf = w / max_freq * np.log2(dcount / df[t])
            # Only store non zero weight terms to optimize the computation
            if tdidf > 0:
                tfidfw.append((t, tdidf))
        tfidfw.sort(key= lambda tup: tup[1])
        tfidf_matrix.append(tfidfw[-R:])

    return tfidf_matrix


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', default=None, required=True, help='Index to search')
    parser.add_argument('--k', default=10, type=int, help='Number of relevant documents to return')
    # **************************************************************************************************************
    # Roccio parameters
    parser.add_argument('--nrounds', default=5, type=int, help='Number of applications of Rocchio’s rule')
    parser.add_argument('--R', default=100, type=int, help='Maximum number of terms to be kept in the new query')
    parser.add_argument('--alpha', default=0.8, type=float, help='Weight in the Rocchio rule for original query')
    parser.add_argument('--beta', default=0.5, type=float, help='Weight in the Rocchio rule for relevant document')
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
    docs = None
    try:
        client = Elasticsearch()
        for ite in range(nrounds):
            print("******************************************************")
            print("iteration", ite + 1)
            q, w = parse_query(query)
            print("Term vector :", q)
            print("Weight vector :", w)
            query = [term + "^" + str(weight) for term, weight in zip(q, w)]
            print("Composed query :", query)
            # Find all relevant documents
            docs = search(client, query, k, index)

            fd = []
            df = defaultdict(int)
            # For each document, compute the term frequency vector and document frequency
            for doc in docs:
                tv = document_term_vector(client, doc.meta.id, index=index)
                # Compute the df from current document set
                for term, _ in tv:
                    df[term] += 1
                fd.append(tv)
            # Compute tf-idf for current document set
            # The data structure is a matrix of pair (term, weight)
            tfidf = toTFIDF(fd, df, R)
            for k in tfidf:
                print(k)



    except NotFoundError:
        print('Index %s does not exists' % index)


