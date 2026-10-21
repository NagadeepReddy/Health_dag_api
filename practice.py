T=$(mktemp /tmp/cta_spawn_XXXXXX.py)
cat > "$T" <<'PY'
import multiprocessing as mp

def worker(queue):
    import pickle
    from cta_spawn_worker import CTAFactoryWrapper

    class DummyFactory:
        def __call__(self):
            return "MODEL"

    factory = CTAFactoryWrapper(DummyFactory())
    restored = pickle.loads(pickle.dumps(factory))
    queue.put(restored.original_factory())

if __name__ == "__main__":
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=worker, args=(q,))
    p.start()
    p.join(8)

    if p.is_alive():
        p.kill()
        p.join()
        raise RuntimeError("Spawn timed out")

    assert p.exitcode == 0, p.exitcode
    assert q.get(timeout=2) == "MODEL"
    print("REAL PYTHON SPAWN: PASS")
PY
PYTHONPATH=artifacts/v1.168-max/maxserve_cta_extension \
timeout 12s python3 "$T"
RC=$?
rm -f "$T"
exit "$RC"
