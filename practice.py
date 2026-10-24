cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

folder = Path("artifacts/v1.168-max/maxserve_cta_extension")
source = folder / "cta_native_startup_test.py"
target = folder / "cta_native_e2e_test.py"

s = source.read_text()
anchor = '        print("CTA PROBE:", response.status_code, response.text, flush=True)\n'

addition = '''
        import json
        from pathlib import Path

        sample = Path("/workspace/artifacts/v1.167/samples/sanity_input.json")
        assert sample.is_file(), f"Missing sample: {sample}"

        body = json.loads(sample.read_text())
        print("SENDING REAL CTA JSON...", flush=True)

        result = client.post("/v2/cta/predict", json=body)
        print("CTA NATIVE HTTP STATUS:", result.status_code, flush=True)
        print("CTA RESPONSE:", result.text[:1200], flush=True)

        assert result.status_code == 200, "Native CTA inference failed"
        print("CTA NATIVE END-TO-END: PASS", flush=True)
'''

assert anchor in s, "Expected startup test structure not found"
target.write_text(s.replace(anchor, anchor + addition, 1))
print("CTA E2E TEST FILE: CREATED")
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py || exit 1

timeout 150s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py

echo "E2E EXIT CODE: $?"
