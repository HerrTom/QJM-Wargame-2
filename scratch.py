import graph_tool as gt
import numpy as np

adj = np.random.randint(0, 2, (100, 100)) # a random directed graph
g = gt.Graph()
g.add_edge_list(nptranspose(adj.nonzero()))