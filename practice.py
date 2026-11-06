
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

export STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
export SHARED="/application1/max_shared_python_deps"
export HANDOFF="/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -d "$STAGE"
test -d "$SHARED"

if [ -e "$HANDOFF" ] || [ -e "${HANDOFF}.tar.gz" ]; then
  echo "STOP: Handoff already exists. Nothing overwritten."
  exit 1
fi

# Give the unchanged shared image a model-independent alias.
ORIGINAL="localhost/cta-max-faiss:local"
NEUTRAL="localhost/max-shared-runtime:cpu"

ORIGINAL_ID=$("${PODMAN[@]}" image inspect --format '{{.Id}}' "$ORIGINAL")

if "${PODMAN[@]}" image exists "$NEUTRAL"; then
  NEUTRAL_ID=$("${PODMAN[@]}" image inspect --format '{{.Id}}' "$NEUTRAL")
  if [ "$ORIGINAL_ID" != "$NEUTRAL_ID" ]; then
    echo "STOP: Neutral MAX image tag points to a different image."
    exit 1
  fi
else
  "${PODMAN[@]}" tag "$ORIGINAL" "$NEUTRAL"
fi

echo "SHARED MAX IMAGE ALIAS: READY"
echo "MAX IMAGE CONTENT: UNCHANGED"

python3 - <<'PY'
import json
import os
import shutil
from pathlib import Path

stage = Path(os.environ["STAGE"])
shared = Path(os.environ["SHARED"])
handoff = Path(os.environ["HANDOFF"])

def ignore(directory, names):
    rel = Path(directory).relative_to(stage)
    excluded = set()

    if rel == Path("."):
        excluded.update({
            "RUNTIME_MANIFEST.json",
            "STAGING_NOTES.md"
        })

    if rel == Path("artifacts/v1.472-max"):
        excluded.add("validation")

    excluded.update(
        name for name in names
        if name in {"__pycache__", ".pytest_cache"}
        or name.endswith((".pyc", ".pyo", ".log"))
    )
    return excluded

print("CREATING CLEAN HANDOFF CANDIDATE", flush=True)

handoff.mkdir(parents=True)

shutil.copytree(
    stage,
    handoff / "model",
    ignore=ignore
)

shutil.copytree(
    shared,
    handoff / "runtime/python_deps",
    ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache",
        "*.pyc", "*.pyo"
    )
)

runtime = handoff / "runtime"
config = handoff / "config"
docs = handoff / "docs"
config.mkdir()
docs.mkdir()

# Model-specific configuration, separate from the common launcher.
(config / "model.env").write_text(
    "MODULE=pzaas_native_serve_dev.pzaas_native_launcher\n"
    "INTERNAL_PORT=18768\n"
    "MODEL_PYTHONPATH="
    "/shared_deps/sklearn161:"
    "/shared_deps:"
    "/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:"
    "/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:"
    "/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:"
    "/workspace/artifacts/v1.472-max:"
    "/workspace/artifacts/v1.472/core-artifact:"
    "/workspace/artifacts/v1.472/utils/dependency-utils\n"
)

launcher = runtime / "launch_max_model.sh"
launcher.write_text(r'''#!/usr/bin/env bash
set -euo pipefail

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE/config/model.env"

HOST_PORT="${HOST_PORT:-18771}"
IMAGE="${IMAGE:-localhost/max-shared-runtime:cpu}"
PODMAN_ROOT="${PODMAN_ROOT:-/application1/podman/storage}"
PODMAN_RUNROOT="${PODMAN_RUNROOT:-/run/containers/storage}"

exec podman \
  --root "$PODMAN_ROOT" \
  --runroot "$PODMAN_RUNROOT" \
  run --rm --pull=never \
  --memory=12g --pids-limit=512 \
  -p "127.0.0.1:${HOST_PORT}:${INTERNAL_PORT}" \
  -v "$BASE/model:/workspace:ro" \
  -v "$BASE/runtime/python_deps:/shared_deps:ro" \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "PYTHONPATH=$MODEL_PYTHONPATH" \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u -m "$MODULE"
''')
launcher.chmod(0o755)

required = [
    "model/artifacts/v1.472/core-artifact/pipeline.py",
    "model/artifacts/v1.472/model-settings.json",
    "model/artifacts/v1.472-max/pzaas_max/pzaas_weight_loader.py",
    "model/artifacts/v1.472-max/pzaas_max/validation/pzaas_forward_schema.json",
    "model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
    "runtime/launch_max_model.sh",
    "config/model.env"
]

for relative in required:
    if not (handoff / relative).is_file():
        raise SystemExit(f"STOP: Required release file missing: {relative}")

source_collection = Path.cwd() / (
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_http_evidence/PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json"
)

if source_collection.is_file():
    shutil.copy2(
        source_collection,
        docs / "PZAAS_Postman_Collection.json"
    )

(docs / "README.md").write_text(
    "# PZAAS v1.472 Modular MAX CPU handoff candidate\n\n"
    "## Structure\n"
    "- model/: Original DS model and isolated MAX integration\n"
    "- runtime/python_deps/: Shared Python dependency snapshot\n"
    "- runtime/launch_max_model.sh: Model-independent MAX launcher\n"
    "- config/model.env: PZAAS-specific serving configuration\n"
    "- docs/: Handoff instructions and Postman collection\n\n"
    "## Run on the prepared VM\n"
    "Ensure the compatible MAX+FAISS image is present as "
    "`localhost/max-shared-runtime:cpu`.\n\n"
    "Run: `HOST_PORT=18771 ./runtime/launch_max_model.sh`\n\n"
    "Endpoint: `POST http://127.0.0.1:18771/pzaas/predict`\n\n"
    "## Verified before packaging\n"
    "- Native trained MAX CPU inference\n"
    "- HTTP 200 and 24 recommendations\n"
    "- Same-input PyTorch/MAX product-list parity\n"
    "- Independent clean-stage HTTP verification\n"
    "- External Postman HTTP 200\n\n"
    "## Not yet certified\n"
    "- Fresh execution from this packaged handoff\n"
    "- Execution on another VM\n"
    "- Approved production container image\n"
    "- Live Kubernetes lookups\n"
    "- GPU, batch-2 and production scaling\n\n"
    "The neutral image alias points to the previously used "
    "development image; it is not a new image build or approval.\n"
    "Adjust Podman storage settings for other hosts.\n"
)

files = [p for p in handoff.rglob("*") if p.is_file()]
size = sum(p.stat().st_size for p in files)

print("CLEAN MODEL + RUNTIME: COPIED")
print("COMMON MAX LAUNCHER: CREATED")
print("MODEL CONFIGURATION: SEPARATED")
print("TOTAL FILES:", len(files))
print("UNCOMPRESSED SIZE GiB:", round(size / 1024**3, 2))
print("HANDOFF:", handoff)
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
PY

python3 - <<'PY'
import hashlib
import os
import tarfile
from pathlib import Path

handoff = Path(os.environ["HANDOFF"])
archive = Path(str(handoff) + ".tar.gz")
temporary = Path(str(archive) + ".part")

with tarfile.open(temporary, "w:gz", compresslevel=3) as tar:
    tar.add(handoff, arcname=handoff.name)

temporary.rename(archive)

digest = hashlib.sha256()
with archive.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)

checksum = Path(str(archive) + ".sha256")
checksum.write_text(
    f"{digest.hexdigest()}  {archive.name}\n"
)

print("HANDOFF ARCHIVE:", archive)
print("SHA256 FILE:", checksum)
print("CLEAN HANDOFF CANDIDATE: CREATED")
print("PACKAGED COLD-START VERIFICATION: PENDING")
print("WORKING POSTMAN CONTAINER: UNCHANGED")
PY
SH
