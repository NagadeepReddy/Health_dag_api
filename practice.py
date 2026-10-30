
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

if "${POD[@]}" container exists "$NAME"; then
  "${POD[@]}" restart --time 15 "$NAME" &&
  echo "ISOLATED MAX: RESTARTED" &&
  "${POD[@]}" inspect --format 'STATUS: {{.State.Status}} | OOM: {{.State.OOMKilled}}' "$NAME" &&
  echo "ORIGINAL MAX: UNTOUCHED" &&
  echo "ORIGINAL DS: UNCHANGED"
else
  echo "STOP: Expected isolated container not found"
fi
