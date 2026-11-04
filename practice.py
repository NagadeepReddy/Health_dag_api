cd /application1/sajjna8/rt-pzaas-v1.0 && {
  echo "=== REQUIRED DEPENDENCIES ==="
  grep -inE 'apscheduler|tzlocal|pytz|python' \
    artifacts/baseimage/requirements.txt \
    artifacts/bplanimage/Dockerfile || true

  echo "=== ORIGINAL DS SCHEDULER INITIALIZATION ==="
  sed -n '565,590p' \
    artifacts/v1.472/core-artifact/pipeline.py

  echo "=== CANDIDATE RUNTIME IMAGES ==="
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    images --format '{{.Repository}}:{{.Tag}}' \
    | grep -Ei 'jarvis|base|pzaas|bplan|cta|max' \
    | head -25

  echo "DEPENDENCY CHECK: COMPLETE"
}
