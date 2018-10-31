#!/usr/bin/python

from pathlib import Path
import time
import numpy as np
import argparse


class Edge:
    def __init__(self, origin=None):
        self.origin = origin  # write appropriate value
        self.weight = 1  # write appropriate value

    def __repr__(self):
        return "edge: {0} {1}".format(self.origin, self.weight)


class Airport:
    def __init__(self, iden=None, name=None):
        self.code = iden
        self.name = name
        self.routes = []
        self.routeHash = dict()
        self.outweight = 0  # write appropriate value
        self.pageIndex = 0

    def __repr__(self):
        return "{0}\t{2}\t{1}".format(self.code, self.name, self.pageIndex)


edgeList = []           # list of Edge
edgeHash = dict()       # hash of edge to ease the match
airportList = []        # list of Airport
airportHash = dict()    # hash key IATA code -> Airport


def read_airports(fd):
    print("Reading Airport file from {0}".format(fd))
    airports_file = open(fd, "r")
    cont = 0
    for line in airports_file.readlines():
        a = Airport()
        try:
            temp = line.split(',')
            if len(temp[4]) != 5:
                raise Exception('not an IATA code')
            a.name = temp[1][1:-1] + ", " + temp[3][1:-1]
            a.code = temp[4][1:-1]
        except Exception:
            pass
        else:
            cont += 1
            airportList.append(a)
            airportHash[a.code] = a
    airports_file.close()
    print("There were {0} Airports with IATA code".format(cont))


def read_routes(fd):
    print("Reading Routes file from {0}".format(fd))
    routes_file = open(fd, "r")
    cont = 0
    for line in routes_file.readlines():
        e = Edge()
        try:
            temp = line.split(',')
            if len(temp[2]) != 3 or len(temp[4]) != 3:
                raise Exception('not an IATA code')
            e.origin = temp[2]
            destination = temp[4]
            # check if aiports codes exist in the airport file
            if e.origin in airportHash and destination in airportHash:
                cont += 1
                # increment the outweight of origin airport
                airportHash[e.origin].outweight += 1
                # append the routes list
                airportHash[destination].routes.append(e)
                # append routeHash of the destination airport if the
                if e.origin in airportHash[destination].routeHash:
                    airportHash[destination].routeHash[e.origin] += 1
                else:
                    airportHash[destination].routeHash[e.origin] = 1
                """
                edgeList.append(e)
                if e.origin+destination not in edgeHash:
                    edgeHash[e.origin+destination] = 1
                else:
                    edgeHash[e.origin+destination] += 1
                """
        except Exception:
            pass
    routes_file.close()
    # normalize weights of edges
    for code, airport in airportHash.items():
        for originCode, routeWeight in airport.routeHash.items():
            airport.routeHash[originCode] = float(routeWeight) / airportHash[originCode].outweight             
    print("There were {0} routes with IATA codes that exist".format(cont))


def compute_page_ranks(L, maxiter, epsilon, verbose):
    # a dictionary which stores the index of each airport and viceversa
    airportIndices = dict()
    index = 0
    for code, airport in airportHash.items():
        airportIndices[code] = index
        airportIndices[index] = code 
        index += 1
    n = len(airportHash)
    P = np.array([1.0/n] * n, np.float64)

    i = 0
    difference = n
    while (i < maxiter and difference > epsilon):
        i += 1
        #print(i)
        #print(sum(P))
        if abs(sum(P)-1.0) > 1e-10:
            raise Exception('sum of pagerank not equals to 1')
        Q = np.array([0.0] * n, np.float64)
        for code, airport in airportHash.items():
            indexDest = airportIndices[code]
            # if airport has no outgoing edge, we have to distribute its pagerank to all
            # nodes including itself
            if airport.outweight == 0:
                auxP = L * P[indexDest]/n
                Q += auxP
            suma = 0.0
            # airports with no incoming edge do not matter since its rank is 0 + (1-L)/n
            for originCode, routeWeight in airport.routeHash.items():
                indexOrig = airportIndices[originCode]
                suma += P[indexOrig] * routeWeight 
            Q[indexDest] += L * suma + (1 - L)/n
        difference = np.linalg.norm(P - Q, 2)
        #print(difference)
        P = Q
    for idx, val in enumerate(P):
        airportHash[airportIndices[idx]].pageIndex = val 
    return i


def outputPageRanks():
    # order the dictionary decreasingly by the pageIndex
    #sorted_d = sorted(airportHash.items(), key=lambda (k, v): v.pageIndex, reverse=True)
    sortedAirports = [(value.code, value.pageIndex) for (key, value) in sorted(airportHash.items(), key=lambda tup: tup[1].pageIndex, reverse=True)]
    #sortedAirports = sorted([(value.pageIndex, key) for (key,value) in airportHash.items()], reverse=True)
    print(sortedAirports[1:10])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-path", default=".", help="Input file directory path")
    parser.add_argument("-max", default="1000", type=int, help="Maximum iteration for Page rank", action="store")
    parser.add_argument("-eps", default="0.0001", type=float, help="Threshold for convergence", action="store")
    parser.add_argument("-df", default="0.9", type=float, help="Dumping factor", action="store")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    parser.add_argument("-w", dest="output_file", action="store", help="write to file")
    args = parser.parse_args()

    data_folder = Path(args.path)
    if not data_folder.exists():
        raise FileExistsError("No data folder found under " + args.path)

    read_airports((data_folder / "airports.txt").absolute())
    read_routes((data_folder / "routes.txt").absolute())

    time1 = time.time()
    iterations = compute_page_ranks(args.df, args.max, args.eps, args.verbose)
    time2 = time.time()
    outputPageRanks()
    print("#Iterations:", iterations)
    print("Time of computePageRanks: {0:.4f} seconds".format(time2-time1))
    

if __name__ == "__main__":
    main()
