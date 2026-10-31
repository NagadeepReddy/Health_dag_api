ps -p 537196 -o pid,ppid,etime,rss,stat,args; cat /proc/537196/cgroup | head -5
