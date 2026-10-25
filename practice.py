cd /application1/sajjna8/rt-pzaas-cta-offers-v1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_check.py <<'PY'
import multiprocessing as mp
import traceback

def original_factory():
    return None

def worker(factory):
    try:
        model = factory()
        print("SPAWNED CTA FACTORY: PASS", type(model).__name__, flush=True)
    except BaseException:
        traceback.print_exc()
        raise

if __name__ == "__main__":
    from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

    ctx = mp.get_context("spawn")
    process = ctx.Process(
        target=worker,
        args=(CTAFactoryWrapper(original_factory),)
    )
    process.start()
    process.join(75)

    if process.is_alive():
        process.terminate()
        process.join()
        print("SPAWNED CTA FACTORY: TIMEOUT")
    else:
        print("SPAWNED CTA FACTORY EXIT:", process.exitcode)
PY

timeout 100s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=4g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_check.py \
  2>&1 | tail -45
