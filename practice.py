ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== NLP WEIGHTS CONFIG ==="
grep -nE 'WEIGHTS|Path|WDIR|BASE|word_embeddings' \
"$ROOT/bplan_max_dev/nlp_bert_max.py"

echo "=== ACTUAL BPLAN WEIGHT ==="
ls -lh "$ROOT/max_weights/nlp_encoder.embeddings.word_embeddings.weight.npy"

echo "=== EXPECTED WEIGHT DIRECTORIES ==="
ls -ld "$ROOT/bplan_max_dev/max_weights" "$ROOT/max_weights" 2>&1
