
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

EXT=artifacts/v1.472-max/maxserve_pzaas_extension

echo "=== PZAAS NATIVE LAUNCHER AND HTTP ROUTES ==="
grep -RnE \
  --include='*.py' \
  'run_module|model-path|--port|1876[0-9]|/v2/|/pzaas|/predict|health|add_route|@.*post|route=' \
  "$EXT/pzaas_native_serve_dev" | head -75 || true

echo "=== AVAILABLE REAL JSON REQUEST FIXTURES ==="
find artifacts/v1.472 artifacts/v1.472-max \
  -type f \( -iname '*input*.json' -o \
             -iname '*request*.json' -o \
             -iname '*sanity*.json' \) \
  2>/dev/null | head -35

echo "=== CTA/BPLAN IMAGE: UNCHANGED ==="
SH
