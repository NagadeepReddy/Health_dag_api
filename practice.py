ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== BPLAN NLP WEIGHT FILES ==="
find "$ROOT" -type f \( \
  -iname '*word*embedding*.npy' -o \
  -iname '*nlp*embedding*.npy' \
\) | head -30

echo "=== NLP WEIGHT PATH IN MAX CODE ==="
grep -nE 'WDIR|BASE|word_embeddings|def nlp_bert_forward|def load' \
"$ROOT/bplan_max_dev/nlp_bert_in_graph.py" | head -35
