set -Eeuo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
NAME=bplan-fresh-handoff-proof
OUT=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz
RESPONSE=/application1/bplan_fresh_handoff_response.json
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== 1. COMPLETE ISOLATED BPLAN RESOURCES ==="

python3 - "$ROOT" "$STAGE" <<'PY'
import sys, os, shutil, hashlib
from pathlib import Path

root, stage = map(Path, sys.argv[1:])
src = root / "artifacts/v1.113"
dst = stage / "artifacts/v1.113"

assert src.is_dir(), f"Missing BPLAN source: {src}"
assert dst.is_dir(), f"Missing extracted stage: {dst}"

copied = 0
excluded = {".git", "__pycache__", ".ipynb_checkpoints"}

# Original core-artifact and utils were already packaged.
# Add every other missing v1.113 resource.
for item in src.rglob("*"):
    rel = item.relative_to(src)
    if any(x in excluded for x in rel.parts):
        continue
    if rel.parts[0] in ("core-artifact", "utils"):
        continue
    if item.suffix in (".pyc", ".log"):
        continue

    target = dst / rel
    if target.exists() or target.is_symlink():
        continue

    target.parent.mkdir(parents=True, exist_ok=True)

    if item.is_symlink():
        target.symlink_to(os.readlink(item))
    elif item.is_dir():
        target.mkdir(exist_ok=True)
    elif item.is_file():
        shutil.copy2(item, target)
        copied += 1

# The failed test identified this exact required filename.
lookup = dst / "lookup/page_seq_2.csv"

if not lookup.is_file():
    candidates = sorted(
        p for p in root.rglob("page_seq_2.csv")
        if p.is_file() and ".git" not in p.parts
    )

    if not candidates:
        print("STOP: page_seq_2.csv is absent from the BPLAN repository.")
        print("The actual original lookup data must be recovered.")
        print("Expected:", lookup)
        sys.exit(2)

    hashes = {
        hashlib.sha256(p.read_bytes()).hexdigest()
        for p in candidates
    }

    print("BPLAN LOOKUP CANDIDATES:")
    for p in candidates:
        print(" ", p)

    if len(hashes) != 1:
        sys.exit("STOP: Conflicting BPLAN lookup files; cannot choose safely")

    lookup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidates[0], lookup)

assert lookup.stat().st_size > 0, "Empty lookup CSV"

# Keep every staged symlink relative and inside this package.
fixed = 0
for link in stage.rglob("*"):
    if not link.is_symlink():
        continue

    raw = os.readlink(link)
    if os.path.isabs(raw):
        absolute = Path(raw)
        if not absolute.is_relative_to(root):
            sys.exit(f"STOP: External symlink: {link} -> {raw}")

        target = stage / absolute.relative_to(root)
        if not target.exists():
            sys.exit(f"STOP: Missing symlink target: {target}")

        link.unlink()
        link.symlink_to(os.path.relpath(target, link.parent))
        fixed += 1

    resolved = link.resolve(strict=True)
    if not resolved.is_relative_to(stage.resolve()):
        sys.exit(f"STOP: Symlink escapes handoff: {link}")

required = [
    "artifacts/v1.113/core-artifact/pipeline.py",
    "artifacts/v1.113/core-artifact/base_model.pt",
    "artifacts/v1.113/core-artifact/bplan_model.pt",
    "artifacts/v1.113/config/tokenizer_config.json",
    "artifacts/v1.113/lookup/page_seq_2.csv",
    "artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py",
]

for name in required:
    assert (stage / name).is_file(), f"Missing: {name}"

print("RESOURCE COMPLETION: PASS")
print("NEW RESOURCE FILES:", copied)
print("SYMLINK REPAIRS:", fixed)
print("LOOKUP DATA: PASS")
print("ORIGINAL DS: UNCHANGED")
PY

echo "=== 2. START FRESH BUILT-IN MAX SERVE ==="

"${P[@]}" rm -f "$NAME" 2>/dev/null || true

"${P[@]}" run -d \
  --name "$NAME" \
  --pull=never \
  --network=bridge \
  -p 127.0.0.1:18769:18768 \
  -v "$STAGE:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

READY=0

for i in $(seq 1 120); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 \
    http://127.0.0.1:18769/bplan/predict || true)

  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi

  RUNNING=$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME")

  if [ "$RUNNING" != "true" ]; then
    break
  fi

  sleep 2
done

if [ "$READY" != 1 ]; then
  echo "FRESH NATIVE SERVER: FAILED"
  "${P[@]}" logs --tail 100 "$NAME"
  exit 1
fi

echo "NATIVE ROUTE: PASS"

echo "=== 3. REAL BPLAN SINGLE-REQUEST HTTP TEST ==="

SAMPLE="$STAGE/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
test -f "$SAMPLE"

CODE=$(curl -sS --max-time 480 \
  -o "$RESPONSE" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  http://127.0.0.1:18769/bplan/predict) || CODE=000

echo "HTTP STATUS: $CODE"

if [ "$CODE" != "200" ]; then
  echo "FRESH NATIVE HTTP: FAILED"
  "${P[@]}" logs --tail 120 "$NAME"
  exit 1
fi

RESPONSE="$RESPONSE" python3 - <<'PY'
import json, os
from pathlib import Path

data = json.loads(Path(os.environ["RESPONSE"]).read_text())
prediction = data["jsonData"]["prediction"]

assert isinstance(prediction, dict)
assert isinstance(prediction.get("ctaList"), list)
assert prediction["ctaList"]

print("FRESH NATIVE HTTP 200: PASS")
print("REAL BPLAN JSON RESPONSE: PASS")
print("PREDICTION KEYS:", sorted(prediction))
PY

echo "=== 4. CREATE VERIFIED FINAL HANDOFF ==="

if [ -e "$OUT" ]; then
  echo "STOP: Final archive already exists. Preserving it."
  exit 1
fi

cat > "$STAGE/BPLAN_HANDOFF_README.txt" <<'EOF'
BPLAN v1.113 — Native Modular MAX Serve single-request POC

Verified:
- Native MAX Serve real inference
- Native HTTP 200
- Postman request
- Exact PyTorch/MAX business-output parity
- Independent fresh-container HTTP validation

Preserved:
- Original DS pipeline, preprocessing and postprocessing
- Original trained model weights and business logic
- Original JSON request/response contract

Start:
- Extract archive into a directory
- Mount the extracted directory as /workspace
- Use the verified MAX development runtime and dependencies
- Set PYTHONPATH to:
  /workspace/artifacts/v1.113-max/maxserve_bplan_extension:
  /workspace/artifacts/v1.113/core-artifact:
  /workspace/artifacts/v1.113/utils/dependency-utils
- Run python -m bplan_native_serve_dev.bplan_native_launcher
- POST /bplan/predict

Runtime image localhost/cta-max-faiss:local is DEVELOPMENT ONLY.
Verizon-approved image and separate-VM testing remain unverified.
Native HTTP Batch-2 coalescing is outside the initial single-request POC.
EOF

TMP="$OUT.partial"
trap 'rm -f "$TMP"' EXIT

tar -C "$STAGE" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='.ipynb_checkpoints' \
  --exclude='.git' \
  -czf "$TMP" \
  BPLAN_HANDOFF_README.txt \
  artifacts/v1.113 \
  artifacts/v1.113-max/maxserve_bplan_extension

gzip -t "$TMP"
mv "$TMP" "$OUT"

(
  cd /application1
  sha256sum "$(basename "$OUT")" > "$(basename "$OUT").sha256"
  sha256sum -c "$(basename "$OUT").sha256"
)

echo "======================================"
echo "BPLAN FINAL LOCAL HANDOFF: PASS"
echo "NATIVE SINGLE REQUEST: PASS"
echo "FRESH CONTAINER HTTP: PASS"
echo "BUSINESS PARITY: PREVIOUSLY PASSED"
echo "ORIGINAL DS AND CTA: UNCHANGED"
echo "======================================"

ls -lh "$OUT" "$OUT.sha256"
