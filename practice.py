cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== DISK SPACE ==="
df -h /var /home /application1

echo "=== REPO STATUS ==="
pwd
git branch --show-current
git status --short --untracked-files=no

echo "=== MAX CODE CHECK ==="
for f in cta_native_launcher.py cta_worker_registration.py cta_spawn_worker.py cta_native_scheduler.py cta_scheduler_factory.py cta_pipeline_model.py cta_architecture_registration.py cta_router.py; do
  test -f "artifacts/v1.168-max/maxserve_cta_extension/$f" && echo "OK: $f" || echo "MISSING: $f"
done
