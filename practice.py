cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --read-only --memory 10g \
--tmpfs /tmp:rw,size=512m \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472-max \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local - <<'PY'
import importlib
import inspect
import traceback

print("=== PZAAS MAX GRAPH BUILD ===", flush=True)

try:
    module = importlib.import_module(
        "pzaas_max.grecbase_fusion_full_head_72_max"
    )
    print("PZAAS GRAPH IMPORT: PASS", flush=True)

    fn = module.build_grecbase_fusion_graph_order_correct
    sig = inspect.signature(fn)
    print("BUILD SIGNATURE:", sig, flush=True)

    required = [
        p.name for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        )
    ]
    if required:
        print("BUILD NEEDS ARGUMENTS:", required)
    else:
        graph = fn()
        print("PZAAS MAX GRAPH BUILD: PASS")
        print("GRAPH TYPE:", type(graph).__name__)
        print("MAX COMPILATION: PENDING")
except Exception:
    print("PZAAS GRAPH BUILD: FAILED")
    traceback.print_exc()
    raise SystemExit(1)
PY
