python3 -B - <<'PY'
from pathlib import Path
import ast, re

pkg = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

patterns = re.compile(
    r"register_cta_routes|register_cta|"
    r"APIType|ROUTES|include_router|"
    r"add_api_route|add_route|\.post\(|\.get\(|"
    r"cta/predict|cta/infer|cta/probe|"
    r"run_module|sys\.argv|max_batch_size|"
    r"custom_router",
    re.I
)

for filename in ("cta_router.py", "cta_native_launcher.py"):
    p = pkg / filename
    print("\n====", filename, "====", flush=True)

    if not p.is_file():
        raise SystemExit("STOP: Missing staged file " + str(p))

    source = p.read_text()
    ast.parse(source)
    lines = source.splitlines()

    shown = set()
    for i, line in enumerate(lines):
        if patterns.search(line):
            for j in range(max(0, i-1), min(len(lines), i+3)):
                if j not in shown:
                    print(f"{j+1}: {lines[j]}")
                    shown.add(j)

    print("SYNTAX: PASS")

print("\nNATIVE ROUTE SOURCE INSPECTION: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
