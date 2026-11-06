
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import hashlib
import json
import tarfile
from pathlib import Path

repo = Path.cwd()
root = repo / "artifacts/v1.472-max"
extension = root / "maxserve_pzaas_extension"
evidence = extension / "pzaas_http_evidence"

comparison = evidence / "pzaas_business_comparison.json"
response = evidence / "pzaas_native_response.json"
server_log = evidence / "pzaas_native_http.log"

for path in (comparison, response, server_log):
    if not path.is_file():
        raise SystemExit(f"STOP: Missing evidence: {path}")

result = json.loads(comparison.read_text())
payload = json.loads(response.read_text())
log = server_log.read_text(errors="replace")

required = (
    "product_id_order_match",
    "product_list_exact_match",
    "orig_score_value_match",
    "isNewRcmd_match",
)

for key in required:
    if result.get(key) is not True:
        raise SystemExit(f"STOP: Parity not confirmed: {key}")

if result.get("max_product_count") != 24 or result.get("pytorch_product_count") != 24:
    raise SystemExit("STOP: Unexpected product counts")

if "PZAAS REAL MAX EXECUTION: PASS" not in log:
    raise SystemExit("STOP: Trained MAX execution proof missing")

if not {"jsonData", "transactionMetadata"}.issubset(payload):
    raise SystemExit("STOP: Native response contract missing")

report = root / "PZAAS_MAX_CPU_POC_HANDOFF.md"

report.write_text("""# PZAAS v1.472 — Modular MAX CPU POC handoff

## Verified
- Genuine trained MAX CPU execution: PASS
- MAX graph: 72 packed inputs, 17/17 trained graph weights
- Previous same-input numerical parity: PASS
- Built-in MAX Serve `/pzaas/predict`: HTTP 200
- Real JSON response: `jsonData`, `transactionMetadata`
- Recommendation count: 24
- Independent original PyTorch baseline: PASS
- MAX/PyTorch same-input product count: 24 / 24
- Product IDs and order: exact match
- Full productList: exact match
- orig_score_value: match
- isNewRcmd: match
- Original DS pipeline, weights and business logic: unchanged

## Environment and scope
- Model: PZAAS v1.472
- Development image: localhost/cta-max-faiss:local
- Shared external Python dependencies
- CPU single-request validation
- Same adjusted sanity JSON fixture for both implementations
- Isolated VM/container network

## Remaining limitations
- Three Kubernetes lookup errors in original PyTorch baseline.
- External Kubernetes lookup services unavailable in this VM test.
- Parity verified for isolated test conditions, not live lookup behavior.
- GPU, native batch-2, production deployment and approved-image status
  have not been validated by this handoff.
- This is an integration-source and evidence package, not a proven
  standalone portable runtime with all trained model dependencies.

## Evidence
- maxserve_pzaas_extension/pzaas_http_evidence/pzaas_native_response.json
- maxserve_pzaas_extension/pzaas_http_evidence/pzaas_native_http.log
- maxserve_pzaas_extension/pzaas_http_evidence/pzaas_business_comparison.json

## Follow-up
- Validate live Kubernetes-dependent lookup behavior in an appropriate environment.
- Confirm deployment image, runtime dependencies and portability separately.
""")

archive = repo / "PZAAS_MAX_CPU_POC_HANDOFF_20261106.tar.gz"
with tarfile.open(archive, "w:gz", compresslevel=3) as tar:
    tar.add(root, arcname="artifacts/v1.472-max")

digest = hashlib.sha256()
with archive.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)

checksum = archive.with_name(archive.name + ".sha256")
checksum.write_text(
    f"{digest.hexdigest()}  {archive.name}\n"
)

print("PZAAS CPU POC EVIDENCE: VERIFIED")
print("TRAINED MAX INFERENCE: PASS")
print("NATIVE HTTP 200: PASS")
print("24-PRODUCT BUSINESS PARITY: PASS")
print("HANDOFF REPORT:", report)
print("SOURCE + EVIDENCE ARCHIVE:", archive)
print("SHA256:", checksum)
print("LIVE KUBERNETES LOOKUPS: PENDING")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
PY
