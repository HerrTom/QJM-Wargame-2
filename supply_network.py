from multiprocessing import Pool

import numpy as np
import scipy.ndimage as ndimage
import networkx as nx
from PIL import Image
import matplotlib.pyplot as plt
from scipy import ndimage

roughDict = {(172,35,167): "urban", (254,230,154): "rolling",
            (186,134,43): "rugged", (255,255,255): "flat",}
waterColour = (37,98,129)
riverColour = (210,238,252)
waterDict = {riverColour: "river", waterColour: "water",
            (255,255,255): "land"}
            
roadDict    = {(0,0,0): "highway", (255,255,255): "none"}

costDict_road  = {"highway": .2, "none": 1}
costDict_terr  = {"flat": 1, "urban": 1.2, "rolling": 1.5, "rugged":  2}
costDict_water = {"land": 1, "river": 10, "water": None}

def get_supply(source,sink,load,graph,size):
    
    traffic = np.zeros(size)
    
    for i, sn in enumerate(sink):
        print("Path from {} to {}".format(source,sn))
        try:
            length, path = nx.multi_source_dijkstra(graph,source,target=sn,weight="weight")
            # path = nx.shortest_path(G,source,sn,weight="weight")
            for coord in path:
                traffic[coord[0],coord[1]] += 1
                # traffic[coord[0],coord[1]] += load[i]
            suppply = length
            print(path)
        except:
            supply = None
    print(traffic.max())
    return supply, traffic
        

def get_neighbours(coords,size):
    # returns a list of valid neighbour coordinates
    val = []
    width, height = size
    i,j = coords
    nb = [-1, 0, 1]
    for xp in nb:
        for yp in nb:
            x = i+xp
            y = j+yp
            if x >= 0 and x < width and y >= 0 and y < height:
                if (x,y) != (i,j):
                    val.append((x,y))
    return val
                
def generate_weighted_graph(roads,water,terrain,ownership,friendlyColour):
    graph = {}
    
    xs, ys = roads.size
    
    dataRoad    = roads.load()
    dataWater   = water.load()
    dataTerr    = terrain.load()
    dataOwn     = ownership.load()
    
    for x in range(xs):
        for y in range(ys):
            neighbours = get_neighbours((x,y),(xs,ys))
            tg = {}
            for nb in neighbours:
                pxRoad = dataRoad[nb[0],nb[1]]
                pxWater = dataWater[nb[0],nb[1]]
                pxTerr = dataTerr[nb[0],nb[1]]
                pxOwn = dataOwn[nb[0],nb[1]]
                
                
                tRoad   = roadDict[pxRoad]
                tWater  = waterDict[pxWater]
                tTerr   = roughDict[pxTerr]
                
                wRoad   = costDict_road[tRoad]
                wWater  = costDict_water[tWater]
                wTerr   = costDict_terr[tTerr]
                
                # check if the pixel is friendly
                if pxOwn == friendlyColour:
                    wOwn = 1
                else:
                    wOwn = None
                
                if (wOwn is not None) and (wWater is not None):
                    tg.update({nb: {"weight": wRoad * wWater * wTerr * wOwn}})
            graph.update({(x,y): tg})
    return nx.Graph(graph)
    
def plot_paths(G,source,sink,size):
    traffic = np.zeros(size)
    
    for sn in sink:
        print("Path from {} to {}".format(source,sn))
        # cons = nx.johnson(G,weight="weight")
        try:
            length, path = nx.multi_source_dijkstra(G,source,target=sn,weight="weight")
            # path = nx.shortest_path(G,source,sn,weight="weight")
            for coord in path:
                traffic[coord[0],coord[1]] += 1
        except:
            print("No path!")
            
    plt.imshow(ndimage.rotate(traffic,90),origin="upper")
   
                
if __name__ == '__main__':
    import os
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    water   = Image.open("./data/germany83/maps/germany1983_water.bmp")
    roads   = Image.open("./data/germany83/maps/germany1983_roads.bmp")
    terr    = Image.open("./data/germany83/maps/germany1983_terrain.bmp")
    own     = Image.open("./data/germany83/maps/germany1983_territory.bmp")
    friendlyColour = (255,0,0)
    
    G = generate_weighted_graph(roads,water,terr,own,friendlyColour)
    
    source = [(1340,500), (1340,800),(1340,200)]
    
    sinks = []
    basesink = (800,500)
    for z in range(50):
        sinks.append((basesink[0]+np.random.randint(-300,300),basesink[1]+np.random.randint(-100,100)))
    print("Generating paths...")
    plot_paths(G,source,sinks,water.size)
    
    
    plt.show()