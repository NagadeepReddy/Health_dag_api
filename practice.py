podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec aal-triton-check python3 -c '
import urllib.request
url = "http://127.0.0.1:8000/v2/models/rt-aal-upg-leads-v1/ready"
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)
try:
    r = opener.open(url, timeout=5)
    print("TRITON MODEL READY:", r.status)
except Exception as e:
    print("READINESS CHECK:", repr(e))
'
