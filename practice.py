cd /application1/sajjna8/rt-pzaas-cta-offers-v1

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

free -h
"${P[@]}" inspect --format 'Memory limit={{.HostConfig.Memory}} OOMKilled={{.State.OOMKilled}}' cta-native-live

if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -ge 9437184 ]; then
    "${P[@]}" update --memory 8g --memory-swap 8g cta-native-live &&
    "${P[@]}" start cta-native-live &&
    sleep 20 &&
    "${P[@]}" logs --tail 65 cta-native-live 2>&1
else
    echo "Not enough available host RAM to safely test 8 GB."
fi
