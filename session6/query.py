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




