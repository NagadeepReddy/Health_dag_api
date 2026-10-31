ss -ltnp '( sport = :18767 )'; ps -eo pid,ppid,stat,args | grep -E '[c]ta_native_launcher|[c]ta_postman_native|[m]axserve' | head -20
