from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .models import SystemGraph
from .graph_service import bfs_levels, CycleError
from .health_service import check_system_health, draw_system_graph

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="System DAG Health API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last: Optional[Dict[str,Any]] = None

@app.get("/")
def home():
    return {"message":"Use POST /health/check"}

@app.post("/health/check")
async def run(system: SystemGraph):
    try:
        levels=bfs_levels(system)
    except CycleError as e:
        raise HTTPException(status_code=400,detail=str(e))
    result=await check_system_health(system,levels)
    result["graph_url"]="/health/graph"
    global _last
    _last={"system":system,"result":result}
    return result

@app.get("/health/table",response_class=HTMLResponse)
async def tbl(req:Request):
    if _last is None: raise HTTPException(400,"Run /health/check first")
    return templates.TemplateResponse("health_table.html",
        {"request":req,
         "overall_status":_last["result"]["overall_status"],
         "nodes":_last["result"]["nodes"]})

@app.get("/health/graph")
async def graph():
    if _last is None: raise HTTPException(400,"Run /health/check first")
    out=BASE/"static"/"graph.png"
    draw_system_graph(_last["system"],_last["result"]["nodes"],str(out))
    return FileResponse(str(out),media_type="image/png")
