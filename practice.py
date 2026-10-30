POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== BATCH-2 BRANCH EVIDENCE ==="

mapfile -t NAMES < <(
  "${POD[@]}" ps -a --format '{{.Names}}' |
  grep '^cta-batch2-' |
  head -n 6
)

if [ "${#NAMES[@]}" -eq 0 ]; then
  echo "STOP: No existing Batch-2 containers found"
else
  for NAME in "${NAMES[@]}"; do
    echo "=== $NAME ==="
    "${POD[@]}" logs --tail 700 "$NAME" 2>&1 |
    grep -E 'CTA BRANCH|TensorValue|ShapeAttr|reshape|new_shape|Operation creation failed' |
    tail -n 35 || true
  done
fi

echo "ORIGINAL DS/MAX: UNCHANGED"
echo "CONTAINERS RESTARTED: NONE"
