podman --root /application1/podman/storage --runroot /run/containers/storage ps --filter id=0c95d4a8f887 --format 'Container: {{.ID}} | Status: {{.Status}}' ; ss -ltn '( sport = :18767 )'
