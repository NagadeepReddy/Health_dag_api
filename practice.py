
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g \
  -v "$PWD:/work:ro" -w /work \
  -e PYTHONPATH=/work/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
import asyncio
from types import SimpleNamespace
from maxserve_cta_extension.cta_router import cta_infer

class TestQueue:
    async def stream(self, request_id, context):
        assert request_id == "cta-test-1"
        assert context.body == {"test_only": True}
        yield SimpleNamespace(
            result={"test_only": "queue-response"}
        )

class TestRequest:
    state = SimpleNamespace(request_id="cta-test-1")
    app = SimpleNamespace(
        state=SimpleNamespace(
            pipeline=SimpleNamespace(
                _engine_queue=TestQueue()
            )
        )
    )
    async def json(self):
        return {"test_only": True}

async def main():
    result = await cta_infer(TestRequest())
    assert result == {"test_only": "queue-response"}
    print("CTA JSON QUEUE INTERFACE: PASS")

asyncio.run(main())
'
