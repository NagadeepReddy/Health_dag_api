python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

base = Path("artifacts/v1.168-max/cta_max")
p = base / "run_real_sanity_max_branch_diag.py"
ref = base / "real_sanity_pytorch_same_input_verified.npz"

if not p.is_file() or not ref.is_file():
    raise SystemExit("STOP: Existing diagnostic or verified reference missing")

s = p.read_text()
marker = "SAME_REAL_INPUT_VERIFIED_COMPARISON"

if marker in s:
    print("VERIFIED COMPARISON ALREADY INSTALLED")
else:
    pattern = re.compile(
        r'(?m)^([ \t]*)if actual\.size != expected\.size:[ \t]*$'
    )
    matches = list(pattern.finditer(s))

    if len(matches) != 1:
        raise SystemExit("STOP: Branch comparison location not unique")

    indent = matches[0].group(1)

    branch_fix = "\n".join([
        indent + "# SAME_REAL_INPUT_VERIFIED_COMPARISON",
        indent + 'if name in ("sequence", "sibling"):',
        indent + '    with np.load(',
        indent + '        BASE / "real_sanity_pytorch_same_input_verified.npz",',
        indent + '        allow_pickle=False',
        indent + '    ) as verified:',
        indent + '        expected = np.asarray(verified[name], dtype=np.float32)',
        indent + '    print(name.upper(), "REFERENCE: VERIFIED SAME REAL INPUT")',
    ]) + "\n"

    s = pattern.sub(
        lambda m: branch_fix + m.group(0), s, count=1
    )

    anchor = 'print("\\nCURRENT BRANCH PARITY:", passed, "/8")'

    if s.count(anchor) != 1:
        raise SystemExit("STOP: Branch summary location not unique")

    final_check = '''
print("\\n=== VERIFIED SAME-INPUT FINAL MODEL PARITY ===")
with np.load(
    BASE / "real_sanity_pytorch_same_input_verified.npz",
    allow_pickle=False
) as verified:
    pt_final = np.asarray(verified["final"], dtype=np.float32)

max_final = np.asarray(outputs[0].to_numpy(), dtype=np.float32)

print("PYTORCH SHAPE:", pt_final.shape)
print("MAX SHAPE:", max_final.shape)

if pt_final.shape != max_final.shape:
    raise RuntimeError("Verified final-output shapes differ")

difference = np.abs(
    pt_final.astype(np.float64) - max_final.astype(np.float64)
)

print("VERIFIED FINAL MAX_DIFF:", float(difference.max()))
print("VERIFIED FINAL MEAN_DIFF:", float(difference.mean()))
print(
    "VERIFIED FINAL MATCH:",
    bool(np.allclose(max_final, pt_final, rtol=1e-3, atol=1e-3))
)
'''

    m = re.search(
        r'(?m)^([ \t]*)'
        + re.escape(anchor)
        + r'[ \t]*$',
        s
    )
    if not m:
        raise SystemExit("STOP: Final comparison insertion point missing")

    summary_indent = m.group(1)
    final_indented = "\n".join(
        summary_indent + line if line else ""
        for line in final_check.strip("\n").splitlines()
    )

    s = s[:m.end()] + "\n\n" + final_indented + s[m.end():]

    ast.parse(s, filename=str(p))

    backup = p.with_suffix(".py.before_verified_comparison")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(s)
    print("VERIFIED COMPARISON ADDED")
    print("BACKUP:", backup)

print("MAX MODEL, ORIGINAL PYTORCH, DS CODE AND WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
