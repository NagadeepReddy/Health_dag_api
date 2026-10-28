echo "=== MAX IMAGE PROVENANCE ==="

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  image inspect \
  localhost/cta-max-faiss:local \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  docker-remote.oneartifactoryci.verizon.com/modular/max-nvidia-full:latest \
  --format 'IMAGE={{.RepoTags}}
ID={{.Id}}
DIGESTS={{.RepoDigests}}
CREATED={{.Created}}
LABELS={{json .Labels}}
---'
