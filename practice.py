ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== SAVED BPLAN PARITY INPUTS ==="
find /bplan_out "$ROOT" -maxdepth 4 -type f \
  \( -name '*neural_inputs.pt' -o \
     -name '*neural_output.pt' -o \
     -name '*baseline.json' \) 2>/dev/null

echo "=== MAX INPUT ADAPTERS ==="
grep -RnE --include='*.py' \
'def .*inputs|def .*infer_max|def .*pack|bplan_neural_inputs|bplan_pytorch_neural_output' \
"$ROOT/bplan_max_dev" | head -35
