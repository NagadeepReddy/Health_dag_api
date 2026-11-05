
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never \
--network=host \
--memory=12g --pids-limit=512 \
-v "$PWD:/workspace:ro" \
-v /application1/max_shared_python_deps:/shared_deps:ro \
-w /workspace \
-e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import traceback

try:
    from pzaas_native_serve_dev.pzaas_spawn_worker import PZAASFactoryWrapper

    print("PZAAS NATIVE FACTORY: PASS", flush=True)

    pipeline = PZAASFactoryWrapper()()

    assert getattr(pipeline, "pzaas_native_adapter", None) is not None
    assert getattr(pipeline, "_pzaas_native_pipeline", False)

    print("PZAAS NATIVE WORKER: PASS", flush=True)
    print("NEXT: BUILT-IN MAX SERVE HTTP 200", flush=True)

except Exception:
    print("PZAAS NATIVE WORKER: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)
PY
