
f=artifacts/v1.168-max/maxserve_cta_extension/PROGRESS.md
if [ -e "$f" ]; then
  echo "TRACKER EXISTS — NOT OVERWRITTEN"
else
  cat > "$f" <<'EOF'
# CTA Modular MAX Serve POC

DONE:
- MAX CPU, 72 inputs, 8/8 parity, 2048 output
- Compiled model caching
- Valid CTA JSON E2E via development FastAPI
- Original tracked DS code unchanged in checked paths
- MAX inference backup verified
- CTA router registration, HTTP probe, CLI preload PASS
- MAX 25.7 Serve internals investigated

PENDING:
P1 Native MAX Serve CTA model/worker integration
P2 Real CTA request through native worker
P3 Native scheduling and batching
P4 Native JSON response validation
P5 CPU/GPU performance
P6 Approved MAX + FAISS image
P7 Original sanity_input.json and final validation

RULES:
- No original DS code changes
- No separate FastAPI as final serving solution
- Preserve completed tests and backups
- Do not repeat completed checks
EOF
  echo "PROGRESS TRACKER CREATED"
fi
