cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
if [ -f artifacts/v1.168-max/cta_max/sequence_weights/fn_norml_g.npy ]; then
  echo "WEIGHTS FILE: FOUND"
  echo "NEXT FIX: set Podman --workdir /workspace"
  ls -lh artifacts/v1.168-max/cta_max/sequence_weights/fn_norml_g.npy
else
  echo "STOP: weights file missing from repository"
fi
