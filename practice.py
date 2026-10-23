cd /application1/sajjna8/rt-pzaas-cta-offers-v1

INPUT=$(find artifacts -type f -name 'sanity_input.json' -print -quit)

if [ -n "$INPUT" ]; then
  echo "Testing real CTA JSON: $INPUT"
  curl -sS -i --max-time 120 \
    -X POST http://127.0.0.1:18080/v2/cta/predict \
    -H "Content-Type: application/json" \
    --data-binary @"$INPUT"
else
  echo "CTA input file not found"
fi
