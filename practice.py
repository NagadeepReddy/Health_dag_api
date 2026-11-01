ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== NLP LOADER ==="
sed -n '1,50p' "$ROOT/bplan_max_dev/nlp_bert_in_graph.py"

echo "=== NLP CALLERS AND WEIGHT ROOTS ==="
grep -RnE --include='*.py' \
'nlp_bert_forward|word_embeddings|WDIR\s*=|BASE\s*=' \
"$ROOT/bplan_max_dev" | cut -c1-230 | head -45
