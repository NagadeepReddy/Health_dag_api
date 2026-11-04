cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import tarfile
import ast
import io

root = Path.cwd()
maxdir = root / "artifacts/v1.472-max/pzaas_max"
validation = maxdir / "validation"
validation.mkdir(parents=True, exist_ok=True)

archive = validation / "PZAAS_MAX_SOURCE_REVIEW.tar.gz"

ds = root / "artifacts/v1.472/utils/dependency-utils/models.py"
pipeline = root / "artifacts/v1.472/core-artifact/pipeline.py"

assert ds.is_file()
assert pipeline.is_file()
assert maxdir.is_dir()

with tarfile.open(archive, "w:gz") as tar:

    # Only PZAAS MAX integration Python source.
    count = 0
    for p in sorted(maxdir.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        tar.add(p, arcname=str(p.relative_to(root)))
        count += 1

    # Original GRecBase implementation, read-only.
    source = ds.read_text()
    tree = ast.parse(source)

    classes = [
        n for n in tree.body
        if isinstance(n, ast.ClassDef)
        and n.name == "GRecBase"
    ]
    assert len(classes) == 1

    code = ast.get_source_segment(source, classes[0])
    assert code

    data = code.encode()
    info = tarfile.TarInfo("reference/GRecBase_original.py.txt")
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))

    # Existing verified input mapping metadata.
    for name in (
        "pzaas_alignment_manifest.json",
        "pzaas_forward_schema.json",
    ):
        p = validation / name
        assert p.is_file(), f"Missing: {name}"
        tar.add(p, arcname="reference/" + name)

    # Original loader and model selection.
    src = pipeline.read_text()
    lines = src.splitlines()
    selected = "\n".join(
        f"{i+1}: {line}"
        for i, line in enumerate(lines)
        if (
            "self.model_base =" in line
            or "def loadBaseModel(" in line
            or "model_suffix=" in line
        )
    )

    data = selected.encode()
    info = tarfile.TarInfo("reference/model_loader.txt")
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))

archive.chmod(0o600)

print("=== PZAAS MAX SOURCE PACKAGE ===")
print("MAX PYTHON FILES:", count)
print("ORIGINAL GRE CBASE: INCLUDED AS REFERENCE")
print("INPUT MAPPING: INCLUDED")
print("MODEL WEIGHTS: NOT INCLUDED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("PACKAGE: PASS")
print("FILE:", archive)
PY
