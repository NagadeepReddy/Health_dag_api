P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== CONTAINER STATUS ==="
"${P[@]}" ps -a --filter name=bplan-debug

echo "=== HTTP ROUTE ==="
curl -sS --max-time 5 \
  -o /tmp/bplan_route_status.txt \
  -w 'HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:18768/bplan/predict
cat /tmp/bplan_route_status.txt 2>/dev/null
echo

echo "=== LATEST SERVER AND WORKER LOGS ==="
"${P[@]}" logs --tail 100 bplan-debug 2>&1
