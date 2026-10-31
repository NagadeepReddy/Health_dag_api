podman --root /application1/podman/storage --runroot /run/containers/storage exec 0c95d4a8f887 sh -c 'echo CPU_STAT; cat /sys/fs/cgroup/cpu.stat; echo CPU_LIMIT; cat /sys/fs/cgroup/cpu.max'
