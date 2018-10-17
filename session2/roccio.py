from __future__ import print_function
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
import argparse
import os
import codecs
from elasticsearch_dsl import Index, analyzer, tokenizer
import glob

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q



def search(q, k, index):
    try:
        client = Elasticsearch()
        s = Search(using=client, index=index)

        if query is not None:
            q = Q('query_string',query=query[0])
            for i in range(1, len(query)):
                q &= Q('query_string',query=query[i])

            s = s.query(q)
            response = s[0:k].execute()
            return response
            #for r in response:  # only returns a specific number of results
            #    print('ID= %s SCORE=%s' % (r.meta.id,  r.meta.score))
            #    print('PATH= %s' % r.path)
            #    print('TEXT: %s' % r.text[:50])
            #    print('-----------------------------------------------------------------')

        else:
            print('No query parameters passed')

    except NotFoundError:
        print('Index %s does not exists' % index)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', default=None, help='Index to search')
    parser.add_argument('--k', default=10, type=int, help='Number of relevant documents to return')
    parser.add_argument('--R', default=10, type=int, help='Maximum number of terms to be kept in the new query')
    parser.add_argument('--nrounds', default=5, type=int, help='Number of applications of Rocchio’s rule')
    parser.add_argument('--alpha', default=0.8, type=float, help='Weight in the Rocchio rule for original query')
    parser.add_argument('--beta', default=0.5, type=float, help='Weight in the Rocchio rule for relevant document')
    parser.add_argument('--query', default=None, nargs=argparse.REMAINDER, help='List of words to search')

    args = parser.parse_args()

    index = args.index
    query = args.query
    print(query)
    k = args.k

    docs = search(query, k, index)
    for r in docs:
        print('ID= %s SCORE=%s' % (r.meta.id, r.meta.score))
        print('PATH= %s' % r.path)
        print('TEXT: %s' % r.text[:50])
        print('-----------------------------------------------------------------')
