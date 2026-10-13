python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "run_real_sanity_max_branch_diag.py"
)

source = p.read_text()
marker = "TASK_REFERENCE_ALIGNED_TO_REAL_INPUTS"

pattern = re.compile(
    r'(?m)^([ \t]*)expected = np\.asarray'
    r'\(references\[name\], dtype=np\.float32\)[ \t]*$'
)

if marker in source:
    print("TASK COMPARISON ALREADY CORRECTED")
else:
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            "STOP: Expected comparison not found. No changes."
        )

    indent = matches[0].group(1)
    lines = [
        "# TASK_REFERENCE_ALIGNED_TO_REAL_INPUTS",
        'if name == "task":',
        '    real = torch.load(',
        '        BASE / "real_sanity_model_in.pt",',
        '        map_location="cpu", weights_only=True',
        '    )',
        '    ids = real["task_in"]',
        '    assert len(ids) == 2',
        '    parts = [',
        '        torch.nn.functional.embedding(',
        '            ids[i].long(),',
        '            state[f"task_embedding.{i}.weight"].float()',
        '        ).reshape(1, -1).detach().cpu().numpy()',
        '        for i in range(2)',
        '    ]',
        '    expected = np.concatenate(parts, axis=1).astype(np.float32)',
        '    print("TASK REFERENCE: SAME REAL INPUT AND CHECKPOINT")',
        'else:',
        '    expected = np.asarray(references[name], dtype=np.float32)',
    ]

    replacement = "\n".join(indent + line for line in lines)

    updated = pattern.sub(
        lambda m: replacement, source, count=1
    )

    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_task_reference_alignment")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)

    print("TASK DIAGNOSTIC REFERENCE ALIGNED")
    print("BACKUP:", backup)

print("MODEL, CHECKPOINT, SAVED REFERENCES AND DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
