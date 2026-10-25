cd /application1/sajjna8/rt-pzaas-cta-offers-v1

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${P[@]}" update --memory 4g --memory-swap 4g cta-native-live &&
"${P[@]}" start cta-native-live &&
sleep 25 &&
"${P[@]}" inspect --format 'Memory={{.HostConfig.Memory}} OOMKilled={{.State.OOMKilled}} Status={{.State.Status}}' cta-native-live &&
"${P[@]}" logs --tail 70 cta-native-live 2>&1
