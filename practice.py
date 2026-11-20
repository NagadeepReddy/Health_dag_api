podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec aal-triton-check \
  python3 -c 'import urllib.request; u="http://127.0.0.1:8000/v2/models/rt-aal-upg-leads-v1/ready"; r=urllib.request.urlopen(u,timeout=5); print("TRITON MODEL READY:",r.status)'
