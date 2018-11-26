import matplotlib.pyplot as plt
import multiprocessing
from networkx import nx
import argparse

K = 0
N = 0


def compute(p):
    while True:
        try:
            G = nx.connected_watts_strogatz_graph(N, K, p)
            sp = nx.average_shortest_path_length(G)
            cl = nx.average_clustering(G)
        except nx.NetworkXError:
            continue
        break
    print("{:>12} {:>12} {:>12} {:12.6f} {:12.6f}".format(N, K, p, sp, cl))
    return sp, cl


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-max', default=10, type=int, help='Max iteration to build the sample data')
    parser.add_argument('-k', default=4, type=int, help='Each node is joined with its `k` nearest neighbors')
    parser.add_argument('-n', default=1024, type=int, help='Number of nodes')

    args = parser.parse_args()
    K = args.k
    N = args.n

    print("Building WS model")
    print("{:>12} {:>12} {:>12} {:>12} {:>12}".format("node", "k", "p", "sp", "cl"))
    p = [1 / 2 ** i for i in range(args.max, -1, -1)]

    pool = multiprocessing.Pool()
    result = pool.map(compute, p)
    pool.close()
    pool.join()
    sp, cl = zip(*result)

    max_sp, max_cl = compute(0)

    plt.plot(p, [s / max_sp for s in sp], 's')
    plt.plot(p, [c / max_cl for c in cl], 'D')
    plt.xlabel("p")
    plt.xscale('log')
    plt.show()
