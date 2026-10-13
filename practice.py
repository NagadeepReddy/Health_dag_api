python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py")
s = p.read_text()
marker = "REAL_INPUT_IHQ_JET_REFERENCE"

if marker in s:
    print("IHQ/JET reference correction already present")
else:
    if 'if name == "task":' not in s:
        raise SystemExit("STOP: Verified Task correction not found")

    pattern = re.compile(
        r'(?m)^([ \t]*)else:\s*\n'
        r'([ \t]*)expected = np\.asarray'
        r'\(references\[name\], dtype=np\.float32\)[ \t]*$'
    )

    matches = list(pattern.finditer(s))
    if len(matches) != 1:
        raise SystemExit(
            "STOP: Expected reference comparison not found exactly once"
        )

    outer, inner = matches[0].group(1, 2)

    code = '''
elif name in ("ihq", "jet"):  # REAL_INPUT_IHQ_JET_REFERENCE
    real = torch.load(
        BASE / "real_sanity_model_in.pt",
        map_location="cpu",
        weights_only=True
    )

    def embedding(ids, weight_name):
        if weight_name not in state:
            raise RuntimeError("Missing trained weight: " + weight_name)
        return torch.nn.functional.embedding(
            torch.as_tensor(ids).long(),
            state[weight_name].float()
        )

    def meanmax(x):
        return torch.cat(
            [x.mean(dim=1), x.max(dim=1).values],
            dim=-1
        )

    with torch.no_grad():
        if name == "ihq":
            value = meanmax(
                embedding(real["ihq_in"], "ihq_embedding.weight")
            )
        else:
            if "jet_in" in real:
                jets = real["jet_in"]
                if isinstance(jets, (list, tuple)) and len(jets) == 2:
                    j0, j1 = jets
                elif torch.is_tensor(jets) and jets.ndim == 3 and jets.shape[0] == 2:
                    j0, j1 = jets[0], jets[1]
                elif torch.is_tensor(jets) and jets.ndim == 3 and jets.shape[1] == 2:
                    j0, j1 = jets[:, 0], jets[:, 1]
                else:
                    raise RuntimeError("Unsupported real jet_in structure")
            elif "jet_name_in" in real and "jet_status_in" in real:
                j0, j1 = real["jet_name_in"], real["jet_status_in"]
            elif "jet_name" in real and "jet_status" in real:
                j0, j1 = real["jet_name"], real["jet_status"]
            else:
                raise RuntimeError(
                    "Real JET inputs not found; no data altered"
                )

            first = meanmax(
                embedding(j0, "jet_embedding.0.weight")
            )
            second = meanmax(
                embedding(j1, "jet_embedding.1.weight")
            )
            value = meanmax(torch.stack([first, second], dim=1))

        expected = value.detach().cpu().numpy().astype(np.float32)

    print(name.upper(), "REFERENCE: REAL INPUT + ORIGINAL CHECKPOINT")
else:
    expected = np.asarray(references[name], dtype=np.float32)
'''

    lines = code.strip("\n").splitlines()
    replacement = "\n".join(
        (outer if line and not line.startswith("    ") else outer + line[:len(line)-len(line.lstrip())])
        + line.lstrip()
        if line else ""
        for line in lines
    )

    updated = pattern.sub(lambda m: replacement, s, count=1)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_ihq_jet_reference_alignment")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("CORRECTED IHQ/JET REFERENCE COMPARISON")
    print("BACKUP:", backup)

print("MAX GRAPH AND ORIGINAL DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
