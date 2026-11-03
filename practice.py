ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== FIND ORIGINAL BPLAN LOOKUP DATA ==="

find /application1 \
  -path /application1/podman -prune -o \
  -type f \( -name 'page_seq_2.csv' -o -name 'page_seq_2.csv.gz' \) \
  -print 2>/dev/null

echo "=== FIND LOOKUP REFERENCES ==="

grep -Rn --include='*.py' \
  'page_seq_2.csv' \
  "$ROOT/artifacts/v1.113" \
  2>/dev/null | head -20

echo "=== EXISTING BPLAN CONTAINERS ==="

"${P[@]}" ps -a --format '{{.Names}} | {{.Status}}' \
  | grep -i bplan || true

echo "=== PREVIOUS CONTAINER MOUNTS ==="

for NAME in bplan-debug bplan-fresh-handoff-proof; do
  if "${P[@]}" container exists "$NAME"; then
    echo "CONTAINER: $NAME"
    "${P[@]}" inspect --format \
      '{{range .Mounts}}{{println .Source "=>" .Destination}}{{end}}' \
      "$NAME"
  fi
done

echo "BPLAN LOOKUP SOURCE INVESTIGATION COMPLETE"
