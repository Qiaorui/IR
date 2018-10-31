#!/usr/bin/python

from collections import namedtuple
import time
import sys
import numpy as np

class Edge:
    def __init__ (self, origin=None):
        self.origin = None # write appropriate value
        self.weight = 1 # write appropriate value

    def __repr__(self):
        return "edge: {0} {1}".format(self.origin, self.weight)

    ## write rest of code that you need for this class

class Airport:
    def __init__ (self, iden=None, name=None):
        self.code = iden
        self.name = name
        self.routes = []
        self.routeHash = dict()
        self.outweight = 0  # write appropriate value
        self.pageIndex = 0
    def __repr__(self):
        return "{0}\t{2}\t{1}".format(self.code, self.name, self.pageIndex)

edgeList = [] # list of Edge
edgeHash = dict() # hash of edge to ease the match
airportList = [] # list of Airport
airportHash = dict() # hash key IATA code -> Airport

def readAirports(fd):
    print ("Reading Airport file from {0}".format(fd))
    airportsTxt = open(fd, "r")
    cont = 0
    for line in airportsTxt.readlines():
        a = Airport()
        try:
            temp = line.split(',')
            if len(temp[4]) != 5:
                raise Exception('not an IATA code')
            a.name=temp[1][1:-1] + ", " + temp[3][1:-1]
            a.code=temp[4][1:-1]
        except Exception as inst:
            pass
        else:
            cont += 1
            airportList.append(a)
            airportHash[a.code] = a
    airportsTxt.close()
    print ("There were {0} Airports with IATA code".format(cont))


def readRoutes(fd):
    print ("Reading Routes file from {0}".format(fd))
    # write your code
    routesTxt = open(fd, "r")
    cont = 0
    for line in routesTxt.readlines():
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
    routesTxt.close()
    # normalize weights of edges
    for code, airport in airportHash.items():
        for originCode, routeWeight in airport.routeHash.items():
            airport.routeHash[originCode] = float(routeWeight) / airportHash[originCode].outweight             
    print ("There were {0} routes with IATA codes that exist".format(cont))

def computePageRanks():
    # a dictionary which stores the index of each airport and viceversa
    airportIndices = dict()
    index = 0
    for code, airport in airportHash.items():
        airportIndices[code] = index
        airportIndices[index] = code 
        index += 1
    n = len(airportHash)
    P = np.array([1.0/n] * n, np.float64)
    L = 0.9
    maxiter = 10
    iter = 0
    epsilon = 1e-4
    difference = n
    #try:
    while (iter < maxiter and difference > epsilon):
        iter += 1
        #print(iter)
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
    return iter
    #except Exception as inst:
     #   print(inst)
    
def outputPageRanks():
    # order the dictionary decreasingly by the pageIndex
    #sorted_d = sorted(airportHash.items(), key=lambda (k, v): v.pageIndex, reverse=True)
    sortedAirports = [(value.code, value.pageIndex) for (key, value) in sorted(airportHash.items(), key=lambda tup: tup[1].pageIndex, reverse=True)]
    #sortedAirports = sorted([(value.pageIndex, key) for (key,value) in airportHash.items()], reverse=True)
    print(sortedAirports[1:10])
    
def main(argv=None):
    readAirports("airports.txt")
    readRoutes("routes.txt")
    
    time1 = time.time()
    iterations = computePageRanks()
    time2 = time.time()
    outputPageRanks()
    print ("#Iterations:", iterations)
    print ("Time of computePageRanks():", time2-time1)
    

if __name__ == "__main__":
    main()
