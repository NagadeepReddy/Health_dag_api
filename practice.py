POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766-10g

echo "=== CONTAINER STATE ==="
"${POD[@]}" inspect "$NAME" --format \
'STATE={{.State.Status}} OOM={{.State.OOMKilled}}'

echo "=== TENSORVALUE ERROR CONTEXT ==="
"${POD[@]}" logs --tail 2500 "$NAME" 2>&1 | python3 -c '
import sys,re
lines=sys.stdin.read().splitlines()
pat=re.compile(r"TensorValue|TypeError|Traceback|Failed to create|graph build|Worker failed",re.I)
hits=[i for i,s in enumerate(lines) if pat.search(s)]
print("MATCHES:",len(hits))
for i in hits[:8]:
    print("\n--- ERROR AT LINE",i+1,"---")
    for s in lines[max(0,i-35):min(len(lines),i+18)]:
        print(s[:1200])
'

echo "=== ACTIVE BATCH-2 GRAPH SOURCE ==="
"${POD[@]}" exec "$NAME" sh -c '
for f in \
/batch2/cta_max/grecbase_fusion_batch2_draft.py \
/batch2/cta_max/grecbase_aux_features_max.py \
/batch2/cta_max/grecbase_aux_branches_max.py; do
  echo "===== $f ====="
  if [ -f "$f" ]; then
    grep -nE "def |for |graph.output|ops.concat|ops.reshape|grecbase_get_path" "$f" | head -65
  fi
done
'

echo "ORIGINAL DS/MAX: UNCHANGED"
