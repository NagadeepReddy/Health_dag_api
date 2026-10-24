cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

start = s.index("async def cta_infer(")
end = s.index("\ndef register_cta_routes(", start)

handler = '''async def cta_infer(request: Request):
    import asyncio
    from fastapi import HTTPException
    from .cta_native_scheduler import CTASerializableOutput

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "CTA request must be a JSON object")

    pipeline = getattr(request.app.state, "pipeline", None)
    queue = getattr(pipeline, "_engine_queue", None)
    if queue is None:
        raise HTTPException(503, "Native MAX worker queue unavailable")

    request_id = request.state.request_id

    try:
        async with asyncio.timeout(120):
            with queue.open_channel(
                request_id,
                {"request_id": request_id, "body": body}
            ) as response_queue:
                while True:
                    output = await response_queue.get()
                    if output is None:
                        continue

                    result = getattr(output, "result", None)
                    if result is None:
                        continue

                    if isinstance(result, CTASerializableOutput):
                        result = result.result

                    if isinstance(result, dict) and "error" in result:
                        raise HTTPException(500, detail=result)

                    return result

    except TimeoutError:
        raise HTTPException(504, "CTA inference timed out")

    raise HTTPException(502, "Native worker returned no CTA result")

'''

updated = s[:start] + handler + s[end:]
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA ROUTER SYNTAX: PASS")
print("CTA RESPONSE UNWRAP: INSTALLED")
print("ORIGINAL DS CODE: UNCHANGED")
PY

if [ $? -eq 0 ]; then
  timeout 150s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never --network=none \
    -v "$PWD:/workspace:Z" \
    -e PYTHONPATH=/workspace/artifacts/v1.168-max \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
    > /tmp/cta_native_final.log 2>&1

  rc=$?
  echo "=== CTA NATIVE RESULTS ==="
  grep -E 'CTA PROBE|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|AssertionError|SyntaxError|ValidationError|Traceback' \
    /tmp/cta_native_final.log | tail -15
  echo "E2E EXIT CODE: $rc"
fi
