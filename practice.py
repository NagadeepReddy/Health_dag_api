
python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

assert "async def cta_infer" not in s, "Inference route already exists"
assert "def register_cta_routes():" in s
assert "    router.add_api_route(" in s

handler = '''
async def cta_infer(request):
    import asyncio
    from fastapi import HTTPException
    from .cta_context import CTAContext

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "CTA request must be a JSON object")

    pipeline = getattr(request.app.state, "pipeline", None)
    queue = getattr(pipeline, "_engine_queue", None)
    if queue is None:
        raise HTTPException(503, "Native MAX worker queue unavailable")

    request_id = request.state.request_id
    context = CTAContext(request_id, body)

    try:
        async with asyncio.timeout(120):
            async for output in queue.stream(request_id, context):
                if output is None:
                    continue
                result = getattr(output, "result", None)
                if result is None:
                    continue
                if isinstance(result, dict) and "error" in result:
                    raise HTTPException(500, detail=result)
                return result
    except TimeoutError:
        raise HTTPException(504, "CTA inference timed out")

    raise HTTPException(502, "Native worker returned no CTA result")


'''

s = s.replace(
    "def register_cta_routes():",
    handler + "def register_cta_routes():",
    1,
)

s = s.replace(
    "    router.add_api_route(",
    '    router.add_api_route("/cta/infer", cta_infer, methods=["POST"])\n'
    "    router.add_api_route(",
    1,
)

compile(s, str(p), "exec")
p.write_text(s)
print("CTA NATIVE ROUTE: ADDED")
print("PYTHON SYNTAX: PASS")
PY
