BUILD_DIR=/tmp/cta-max-faiss-build
mkdir -p "$BUILD_DIR" &&
cp /vzwhome/sajjna8/faiss_cpu-1.15.1-cp310-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl "$BUILD_DIR/" &&
cat > "$BUILD_DIR/Containerfile" <<'EOF'
FROM docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest
USER 0
COPY faiss_cpu*.whl /tmp/
RUN python3 -m pip install --no-index --no-deps /tmp/faiss_cpu*.whl \
 && python3 -c "import faiss; print('FAISS IMPORT: PASS', faiss.__version__)" \
 && rm /tmp/faiss_cpu*.whl
EOF
podman build --pull=never -t cta-max-faiss:local "$BUILD_DIR"
