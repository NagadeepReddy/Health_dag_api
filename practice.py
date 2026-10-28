ps -eo pid,ppid,stat,rss,args | grep -E '[m]ax.entrypoints.pipelines|[c]ta_native_launcher|[m]odel_worker'
