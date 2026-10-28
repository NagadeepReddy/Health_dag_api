awk '
/MemAvailable:/ {ram=$2}
/SwapFree:/ {swap=$2}
END {
  printf "Available RAM: %.2f GiB\n", ram/1048576
  printf "Free swap: %.2f GiB\n", swap/1048576
  if (ram >= 6291456)
    print "MEMORY CHECK: PASS for considering a controlled 4 GiB test"
  else
    print "MEMORY CHECK: STOP - insufficient RAM for a safe 4 GiB test"
}' /proc/meminfo
