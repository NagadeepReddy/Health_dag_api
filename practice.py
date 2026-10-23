set -e

W=/vzwhome/sajjna8/faiss_cpu-1.15.1-cp310-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
test -s "$W" || { echo "FAISS WHEEL MISSING"; exit 1; }

D=$(mktemp -d /tmp/cta-faiss-build-XXXXXX)
cp "$W" "$D/"

cat > "$D/Containerfile" <<'EOF'
FROM f30453065dac
USER 0
COPY faiss_cpu-*.whl /tmp/
RUN /opt/venv/bin/python -m pip install --no-index --no-deps /tmp/faiss_cpu-*.whl && \
    /opt/venv/bin/python -c "import faiss; from max.engine import InferenceSession; print('MAX + FAISS: PASS', faiss.__version__)"
EOF

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  build --pull=never --network=none \
  --memory=4g --pids-limit=32 \
  -t cta-max-faiss:local \
  -f "$D/Containerfile" "$D"
