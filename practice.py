echo "NATIVE API ROUTES:"
curl -sS --max-time 5 http://127.0.0.1:18767/openapi.json | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(m.upper(),p) for p,ms in d.get("paths",{}).items() for m in ms]'

echo "LATEST MAX LOG:"
podman --root /application1/podman/storage --runroot /run/containers/storage exec 0c95d4a8f887 tail -n 65 /tmp/cta_postman_native_18767.log
