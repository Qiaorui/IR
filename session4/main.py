import sys

import matplotlib.pyplot as plt
import multiprocessing
from networkx import nx
import math

E = 0.4


def find_p(n):
    return (1 + E) * math.log(n) / n


def calculate_avg_sp_length(n):
    p = find_p(n)
    m = math.ceil(n * (n - 1) / 2 * p)
    G = nx.gnm_random_graph(n, m)
    sp = nx.average_shortest_path_length(G)
    print("node :{}\t\tedge:{}\t\tp:{}\t\tsp:{}".format(n, m, p, sp))
    return sp


if __name__ == '__main__':
    print("Building ER model")
    nodes = [10 * 2 ** i for i in range(21)]
    sp = []
    for n in nodes:
        sp.append(calculate_avg_sp_length(n))

    plt.plot(nodes, sp, 'o-')
    plt.ylabel("average shortest path")
    plt.xlabel("num nodes")
    plt.xlim(0, max(nodes))
    plt.ylim(0, math.ceil(max(sp)))
    plt.show()

    """
    #cl = []
    pool = multiprocessing.Pool()
    result = pool.map_async(calculate_avg_sp_length, nodes)
    pool.close()
    pool.join()
    
    print(result.get())
    """
