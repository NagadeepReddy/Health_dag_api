ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts
echo "=== NATIVE MODEL DIRECTORY ==="
find "$ROOT/v1.113-max/maxserve_bplan_extension" -maxdepth 4 \( -name config.json -o -name bplan_native_model \) -print
echo "=== ORIGINAL MODEL CONFIG ==="
ls -l "$ROOT/v1.113/config/config.json"
echo "=== BPLAN REGISTRATION ==="
grep -nE 'name=|model_path|architecture|register' "$ROOT/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_architecture_registration.py"
