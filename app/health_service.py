import asyncio
from typing import Dict, List
import httpx
import networkx as nx
import matplotlib.pyplot as plt
from .models import SystemGraph, Node

async def _check_single_node(node: Node):
    status="UP"; detail="OK"
    if node.health_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r=await client.get(node.health_url)
            if r.status_code!=200:
                status="DOWN"; detail=f"HTTP {r.status_code}"
        except Exception as exc:
            status="DOWN"; detail=str(exc)
    return {"id":node.id,"name":node.name,"status":status,"detail":detail}

async def check_system_health(system: SystemGraph, levels: Dict[str,int]):
    tasks=[_check_single_node(n) for n in system.nodes]
    results=await asyncio.gather(*tasks)
    for r in results:
        r["level"]=levels.get(r["id"],0)

    def num(x): return int(x.replace("step",""))
    results.sort(key=lambda r:(r["level"],num(r["id"])))

    overall="UP"
    if any(r["status"]=="DOWN" for r in results):
        overall="DEGRADED"

    return {"overall_status":overall,"nodes":results}

def draw_system_graph(system: SystemGraph, results: List[Dict], out):
    status={n["id"]:n["status"] for n in results}
    g=nx.DiGraph()
    for n in system.nodes: g.add_node(n.id,label=n.name)
    for e in system.edges: g.add_edge(e.source,e.target)
    colors=["red" if status[n]=="DOWN" else "lightgreen" for n in g.nodes()]
    plt.figure(figsize=(10,4))
    pos=nx.spring_layout(g,seed=42)
    nx.draw(g,pos,with_labels=True,labels={n:g.nodes[n]["label"] for n in g.nodes()},node_color=colors,arrows=True)
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out
