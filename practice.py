CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
export PODMAN_ROOT=/application1/podman/storage
export PODMAN_RUNROOT=/run/containers/storage
export CTA_IMAGE=localhost/cta-max-faiss:local

PODMAN=(podman --root "$PODMAN_ROOT" --runroot "$PODMAN_RUNROOT")

bash "$CLEAN/run_cta_native.sh" check || exit 1

if "${PODMAN[@]}" container exists cta-postman-shm1g-test; then
  STATUS=$("${PODMAN[@]}" inspect cta-postman-shm1g-test \
    --format '{{.State.Status}}')

  if [ "$STATUS" = running ]; then
    "${PODMAN[@]}" stop --time 20 cta-postman-shm1g-test || exit 1
  fi
fi

echo "=== START CLEAN VM PACKAGE ==="
bash "$CLEAN/run_cta_native.sh" start
