mkdir -p /vzwhome/sajjna8/cta-max-code-review && \
cp -r ../cta-max-release-review/artifacts/v1.168-max/cta_max \
/vzwhome/sajjna8/cta-max-code-review/ && \
chown -R sajjna8:$(id -gn sajjna8) \
/vzwhome/sajjna8/cta-max-code-review
