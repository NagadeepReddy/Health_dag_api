echo "PORT CHECK:"
ss -ltn '( sport = :18767 )'
echo "NATIVE HEALTH:"
curl -sS --max-time 5 -o /dev/null -w 'HTTP STATUS: %{http_code}\n' http://127.0.0.1:18767/health
echo "LATEST STARTUP LOG:"
podman --root /application1/podman/storage --runroot /run/containers/storage exec 0c95d4a8f887 tail -n 15 /tmp/cta_postman_native_18767.log
