ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== NATIVE LAUNCHER ==="
sed -n '1,220p' "$ROOT/run_cta_native.sh"

echo "=== LAUNCHER DEPENDENCIES ==="
grep -nE \
  'application1|batch2|workspace|podman|mount|volume|18767|cta_max|real_max' \
  "$ROOT/run_cta_native.sh"
