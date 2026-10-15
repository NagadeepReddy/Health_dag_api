python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/.gitignore")

if p.exists():
    print("GITIGNORE ALREADY EXISTS — NO CHANGES")
else:
    p.write_text(
        "__pycache__/\n"
        "*.pyc\n"
        ".pytest_cache/\n"
        "test-results/\n"
        "*.bak\n"
        "*.before_*\n"
    )
    print("MAX GITIGNORE: READY")
    print("MODEL WEIGHTS: UNCHANGED")
    print("ORIGINAL DS CODE: UNCHANGED")
    print("NO FILES DELETED")
PY
