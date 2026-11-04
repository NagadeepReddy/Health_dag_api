cd /application1/sajjna8/rt-pzaas-v1.0 && {
  echo "=== LOCAL DS MODULES ==="
  for m in bplan dynamic_offer fwa helper ngd_pros pricing pros_plan_perk rt_churn; do
    find artifacts/v1.472 -type d -name "$m" -print | head -3
  done

  echo "=== MODEL RUNTIME IMAGES ==="
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    images --format '{{.Repository}}:{{.Tag}}' |
    grep -Ei 'pzaas|pytorch|torch|triton|mlserver|truefoundry|modular|max|model-serving|python' |
    grep -Ev 'gateway|aggregator' | sort -u | head -40

  echo "=== AVAILABLE OFFLINE PACKAGES ==="
  find /application1 /opt \
    -type f \( -iname 'einops*.whl' \
    -o -iname 'apscheduler*.whl' \
    -o -iname 'scikit_learn*.whl' \) \
    -print 2>/dev/null | head -20

  echo "RUNTIME DISCOVERY: COMPLETE"
}
