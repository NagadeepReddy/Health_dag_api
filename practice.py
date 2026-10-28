cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import re

log = Path("/application1/cta_native_bridge_validation.log")
report = Path("/application1/CTA_MAX_CPU_BASELINE_20261028.txt")

assert log.is_file(), "STOP: Successful E2E log missing"
assert not report.exists(), "STOP: Baseline report already exists"

s = log.read_text(errors="replace")

checks = {
    "Native HTTP 200": bool(re.search(
        r"CTA NATIVE HTTP STATUS:\s*200", s)),
    "Native E2E PASS": "CTA NATIVE END-TO-END: PASS" in s,
    "Real MAX inference": "MAX INFERENCE EXECUTED:" in s,
    "Response queue sent": "CTA RESPONSE QUEUE SEND: COMPLETED" in s,
}

assert all(checks.values()), "STOP: E2E evidence incomplete"

metrics = {}
for label, pattern in {
    "Prediction duration (seconds)":
        r"CTA PREDICT_RAW:\s*ELAPSED\s*([\d.]+)s",
    "Preprocessing duration (seconds)":
        r"CTA preprocess:\s*ELAPSED\s*([\d.]+)s",
    "Postprocessing duration (seconds)":
        r"CTA postprocess:\s*ELAPSED\s*([\d.]+)s",
}.items():
    values = re.findall(pattern, s, re.I)
    metrics[label] = values[-1] if values else "NOT RECORDED"

lines = [
    "CTA MAX — NATIVE CPU PERFORMANCE BASELINE",
    "Evidence: " + str(log),
    "",
    "VALIDATED RESULTS",
]
lines += [f"{k}: PASS" for k in checks]
lines += ["", "RECORDED TIMINGS"]
lines += [f"{k}: {v}" for k, v in metrics.items()]
lines += [
    "",
    "Single-request functional baseline only.",
    "Concurrent throughput: NOT YET MEASURED",
    "P95/P99 latency: NOT YET MEASURED",
    "True batched inference: NOT IMPLEMENTED",
    "GPU performance: NOT TESTED",
    "Original DS code: UNCHANGED",
]

report.write_text("\n".join(lines) + "\n")

print("\n".join(lines))
print("\nCPU BASELINE REPORT: CREATED")
print("NO MODEL STARTUP")
print("NO WORKING CODE MODIFIED")
PY
