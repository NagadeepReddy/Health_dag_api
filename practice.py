FILE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_projection_parity.py

if [ -f "$FILE" ]; then
  echo "=== EXISTING BPLAN PARITY TEST ==="
  sed -n '1,260p' "$FILE"
else
  echo "STOP: Parity script not found"
fi
