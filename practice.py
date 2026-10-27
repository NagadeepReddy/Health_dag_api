cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -RnE -m 3 \
'compatible weights|unsupported architecture|q4_k|Worker failed|Traceback' \
artifacts/v1.168-max \
--include='*.log' --include='*.txt' --include='*.md' \
2>/dev/null | head -35
