cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -Rn -C 5 -E \
'ProcessMonitor|worker_monitor|register_process|register_worker|is_healthy|spawn_worker' \
artifacts/v1.168-max/maxserve_cta_extension/ \
--include='*.py' | tail -110
