from collections import defaultdict, deque
from typing import Dict, List, Tuple
from .models import SystemGraph

class CycleError(Exception):
    pass

def build_adjacency(system: SystemGraph):
    adjacency=defaultdict(list)
    in_deg=defaultdict(int)
    for n in system.nodes:
        in_deg[n.id]=0
    for e in system.edges:
        adjacency[e.source].append(e.target)
        in_deg[e.target]+=1
    return adjacency,in_deg

def bfs_levels(system: SystemGraph):
    adj, indeg = build_adjacency(system)
    q=deque()
    level={}
    for n in system.nodes:
        if indeg[n.id]==0:
            q.append(n.id)
            level[n.id]=0
    visited=0
    while q:
        cur=q.popleft()
        visited+=1
        for nb in adj[cur]:
            indeg[nb]-=1
            if indeg[nb]==0:
                level[nb]=level[cur]+1
                q.append(nb)
    if visited!=len(system.nodes):
        raise CycleError("Graph contains a cycle.")
    return level
