
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i \
--pull=never \
--network=none \
--memory=12g \
--pids-limit=512 \
-v "$PWD:/workspace:ro" \
-w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import traceback

print("=== PZAAS REAL NATIVE WORKER INITIALIZATION ===", flush=True)

try:
    from pzaas_native_serve_dev.pzaas_spawn_worker import PZAASFactoryWrapper
    print("NATIVE FACTORY IMPORT: PASS", flush=True)

    factory = PZAASFactoryWrapper()
    print("NATIVE FACTORY: CREATED", flush=True)

    pipeline = factory()
    print("REAL NATIVE WORKER INITIALIZATION: PASS", flush=True)

    adapter = getattr(pipeline, "pzaas_native_adapter", None)
    assert adapter is not None, "Native worker not attached"
    print("NATIVE WORKER ATTACHED: PASS", flush=True)

    assert getattr(pipeline, "_pzaas_native_pipeline", False), \
        "Native pipeline registration missing"

    print("NATIVE PIPELINE REGISTRATION: PASS", flush=True)
    print("NEXT: START BUILT-IN MAX SERVE AND VERIFY HTTP 200", flush=True)

except Exception:
    print("NATIVE WORKER INITIALIZATION: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)

finally:
    print("ORIGINAL DS / CTA / BPLAN: NOT MODIFIED BY THIS TEST", flush=True)
PY
