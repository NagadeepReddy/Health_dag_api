cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== STOP OLD CTA TESTS ==="
ps -eo pid,args | awk \
  '$0 ~ /[c]ta_native_e2e_test.py/ && $0 ~ /[/]opt[/]venv[/]bin[/]python/ {print $1}' \
  | xargs -r kill -TERM

echo "=== FIRST REQUEST PROCESSING RESULTS ==="
grep -nE 'CTA REQUEST RECEIVED|CTA MAX REQUEST UNWRAPPED|CTA WORKER RESPONSE IDS|KeyError|TypeError|ValueError|RuntimeError|Exception' \
  /tmp/cta_queue_fix_test.log | grep -v 'RESPONSE IDS: \[\]' | head -25
