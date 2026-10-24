podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect, max.serve.api_server as m; print("STARTUP FUNCTIONS:"); [print(n, inspect.signature(v)) for n,v in vars(m).items() if inspect.isfunction(v) and ("serve" in n or "start" in n or "worker" in n)]'
