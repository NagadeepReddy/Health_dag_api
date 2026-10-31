echo "=== HOST MEMORY ==="
free -h

echo "=== APPLICATION DISK ==="
df -h /application1

echo "=== MAX TEST IMAGE ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format '{{.Repository}}:{{.Tag}} | {{.Size}}' \
  | grep 'cta-max-faiss'

echo "=== CLEAN PACKAGE ==="
test -f /application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/real_max_batch2_backend.py \
  && echo "CLEAN BACKEND: PRESENT"

test -f /application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/run_batch2_contract.py \
  && echo "BATCH HELPER: PRESENT"
