DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

dev = Path(os.environ["DEV"])
target = dev / "bplan_router.py"

assert (dev / "bplan_context.py").is_file()
assert (dev / "bplan_native_scheduler.py").is_file()
assert not target.exists(), "STOP: router already exists"

code = '''"""BPLAN-only HTTP routes within native MAX Serve."""

import asyncio
from uuid import uuid4
from fastapi import Request, HTTPException
from max.interfaces.request import RequestID
from max.serve.api_server import ROUTES
from max.serve.config import APIType

from .bplan_context import BPlanContext
from .bplan_native_scheduler import BPlanSerializableOutput


async def bplan_predict(request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "BPLAN request must be a JSON object")

    pipeline = getattr(request.app.state, "pipeline", None)
    queue = getattr(pipeline, "_engine_queue", None)
    if queue is None:
        raise HTTPException(503, "BPLAN native MAX queue unavailable")

    request_id = str(getattr(request.state, "request_id", None) or uuid4())

    try:
        async with asyncio.timeout(480):
            with queue.open_channel(
                RequestID(request_id),
                BPlanContext(request_id, body),
            ) as response_queue:
                while True:
                    output = await response_queue.get()
                    if output is None:
                        continue
                    result = getattr(output, "result", None)
                    if isinstance(result, BPlanSerializableOutput):
                        result = result.result
                    if isinstance(result, dict) and "error" in result:
                        raise HTTPException(500, detail=result)
                    if result is not None:
                        return result
    except TimeoutError:
        raise HTTPException(504, "BPLAN inference timed out")


def register_bplan_routes():
    router = ROUTES[APIType.KSERVE].router
    if any(r.path == "/bplan/predict" for r in router.routes):
        return False
    router.add_api_route("/bplan/predict", bplan_predict, methods=["POST"])
    return True
'''

ast.parse(code)
target.write_text(code)
print("BPLAN NATIVE HTTP ROUTER: CREATED")
print("BPLAN ROUTER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
