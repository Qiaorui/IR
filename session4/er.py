import matplotlib.pyplot as plt
import multiprocessing
from networkx import nx
import math
import argparse

E = 0


def find_p(n):
    return (1 + E) * math.log(n) / n


def calculate_avg_sp_length(n):
    p = find_p(n)
    m = math.ceil(n * (n - 1) / 2 * p)
    while True:
        try:
            G = nx.gnm_random_graph(n, m)
            sp = nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            continue
        break
    print("{:>12} {:>12} {:12.6f} {:12.6f}".format(n, m, p, sp))
    return sp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-max', default=10, type=int, help='Max iteration to build the graph')
    parser.add_argument('-e', default=0.05, type=float, help='e parameter to configure p value')

    args = parser.parse_args()
    E = args.e

    print("Building ER model")
    print("{:>12} {:>12} {:>12} {:>12}".format("node", "edge", "p", "sp"))
    nodes = [10 * 2 ** i for i in range(args.max)]

    pool = multiprocessing.Pool()
    result = pool.map(calculate_avg_sp_length, nodes)
    pool.close()
    pool.join()
    sp = result

    plt.plot(nodes, sp, 'o-')
    plt.ylabel("average shortest path")
    plt.xlabel("num nodes")
    plt.xlim(0, max(nodes))
    plt.ylim(0, math.ceil(max(sp)))
    plt.show()
