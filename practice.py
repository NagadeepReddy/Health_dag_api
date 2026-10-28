cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
printf '\n=== AVAILABLE RAM ===\n' && \
free -h && \
printf '\n=== APPLICATION1 DISK ===\n' && \
df -h /application1 && \
printf '\n=== EXISTING CTA TEST PROCESSES ===\n' && \
ps -eo pid,ppid,stat,rss,args \
| grep -E '[c]ta_native_e2e_test.py|[c]ta_spawn_worker.py' \
|| true
