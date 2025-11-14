from typing import List, Optional
from pydantic import BaseModel, Field

class Node(BaseModel):
    id: str
    name: str
    health_url: Optional[str] = None

class Edge(BaseModel):
    source: str
    target: str

class SystemGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
