from networkx import nx
import matplotlib.pyplot as plt
import csv
import collections
import math
import powerlaw

import warnings
warnings.filterwarnings("ignore")


def read(path, d):
    with open(path, newline='') as f:
        reader = csv.reader(f, delimiter=d)
        return [(row[0], row[1]) for row in reader]


if __name__ == '__main__':
    data = read("Simple_pairwise-London_tube_map.txt", "\t")
    g = nx.Graph(data)
    n, m = g.number_of_nodes(), g.number_of_edges()
    p = m/((n - 1)*n/2)
    diameter = nx.diameter(g)
    c = nx.average_clustering(g)

    degree_sequence = sorted([d for n, d in g.degree()], reverse=True)  # degree sequence
    degreeCount = collections.Counter(degree_sequence)
    deg, cnt = zip(*degreeCount.items())

    print("Node size: {}\t\tEdge size: {}".format(n, m))
    print("p:{:10.6f}".format(p))
    print("diameter:{:10.6f}".format(diameter))
    print("average shortest path length:{:10.6f}".format(nx.average_shortest_path_length(g)))
    print("clustering coefficient:{:10.6f}".format(c))

    fig, ax = plt.subplots()
    plt.bar(deg, cnt, width=0.80, color='b')
    plt.title("Degree Histogram")
    plt.ylabel("Count")
    plt.xlabel("Degree")
    ax.set_xticks([d for d in deg])
    ax.set_xticklabels(deg)
    plt.show()

    print("**************** Real World Test ****************")
    print("{:<20}{}".format("Small diameter", math.log(n) > diameter))
    print("{:<20}{}".format("High clustering", c > p))
    fit = powerlaw.Fit(degree_sequence, xmin=1)
    print("Power Law test: alpha:{:10.6f}\t\tsigma:{:10.6f}".format(fit.alpha, fit.sigma))
    print("{:<20}{}".format("Power law ", fit.alpha > 2))
    print("*************************************************")

    plt.figure(figsize=(20, 20))
    nx.draw_kamada_kawai(g, with_labels=True, node_size=20, font_size=8, alpha=0.5, node_color="blue")
    plt.show()
