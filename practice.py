ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== NLP WEIGHT LOADING CODE ==="
grep -Rsn --include='*.py' \
  -E 'Missing NLP weight|nlp_encoder.embeddings.word_embeddings.weight' \
  "$ROOT/batch2/cta_max" \
  "$ROOT/artifacts/v1.168-max/cta_max" \
  "$ORIG" 2>/dev/null | head -25

echo "=== NLP WEIGHTS AND CHECKPOINTS ==="
find "$ROOT/batch2/cta_max" \
     "$ROOT/artifacts/v1.168-max/cta_max" \
     "$ORIG" \
     "$REPO/artifacts/v1.168-max" \
  -type f \( \
    -iname '*nlp*' -o \
    -iname '*word*embed*' -o \
    -name '*.safetensors' -o \
    -name 'model_0_base.pt' \
  \) -print 2>/dev/null | head -65
