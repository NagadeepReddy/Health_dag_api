podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-clean-batch2-http-20261030 \
  --format 'COMMAND={{json .Config.Cmd}} ENTRYPOINT={{json .Config.Entrypoint}}'
