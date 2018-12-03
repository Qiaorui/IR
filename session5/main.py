from networkx import nx
import matplotlib.pyplot as plt
import csv
import collections
import math
import powerlaw
import community
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

    print("************** Network Description **************")
    print("Node size: {}\t\tEdge size: {}".format(n, m))
    print("p:{:10.6f}".format(p))
    print("diameter:{:10.6f}".format(diameter))
    print("average shortest path length:{:10.6f}".format(nx.average_shortest_path_length(g)))
    print("clustering coefficient:{:10.6f}".format(c))
    fit = powerlaw.Fit(degree_sequence, xmin=1)
    print("Power Law test: alpha:{:10.6f}\t\tsigma:{:10.6f}".format(fit.alpha, fit.sigma))

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
    print("{:<20}{}".format("Power law ", fit.alpha < 3))
    print("******************* Page Rank *******************")
    pr = nx.pagerank(g)
    max_color = max(pr.values())
    color_list = [1 - value/max_color for value in pr.values()]
    sorted_pr = sorted(pr.items(), key=lambda tup: (tup[1], tup[0]))
    for key, value in reversed(sorted_pr[-10:]):
        print("{:<30}:{:10.6f}".format(key, value))

    plt.figure(figsize=(10, 10))
    nx.draw_kamada_kawai(g, node_size=20, node_color=color_list, cmap=plt.cm.Reds_r)
    plt.show()
    print("************** Community Detection **************")
    partition = community.best_partition(g)
    partition_count = collections.Counter(list(partition.values()))
    for i, count in sorted(partition_count.items(), key=lambda tup: tup[1]):
        print("Group {:<3}\t{}".format(i+1, count))
    pos = nx.kamada_kawai_layout(g)

    fig, ax = plt.subplots()
    plt.bar(partition_count.keys(), partition_count.values(), width=0.80, color='b')
    plt.title("Community Size Histogram")
    plt.ylabel("Size")
    plt.xlabel("Group")
    ax.set_xticks([d for d in partition_count.keys()])
    ax.set_xticklabels([c+1 for c in partition_count.keys()])
    plt.show()

    plt.figure(figsize=(10, 10))
    nx.draw_networkx_edges(g, pos, alpha=0.5)
    nx.draw_networkx_nodes(g, pos, node_color=list(partition.values()), with_labels=False, node_size=20, cmap=plt.cm.jet)
    plt.axis('off')
    plt.show()