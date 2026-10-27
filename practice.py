cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== 1. DISK SPACE ==="
df -h /application1
df -i /application1

echo "=== 2. REPO / GIT ==="
pwd
git branch --show-current
git status --short --untracked-files=no

echo "=== 3. CRITICAL MAX FILES ==="
for f in \
  cta_native_launcher.py \
  cta_worker_registration.py \
  cta_spawn_worker.py \
  cta_native_scheduler.py \
  cta_scheduler_factory.py \
  cta_pipeline_model.py \
  cta_architecture_registration.py \
  cta_router.py
do
  if [ -f "artifacts/v1.168-max/maxserve_cta_extension/$f" ]; then
    echo "EXISTS: $f"
  else
    echo "MISSING: $f"
  fi
done

echo "=== CHECK COMPLETE ==="
