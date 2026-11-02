curl -sS --max-time 5 \
  -o /tmp/bplan_route_check.txt \
  -w 'BPLAN ROUTE HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:18768/bplan/predict

cat /tmp/bplan_route_check.txt
