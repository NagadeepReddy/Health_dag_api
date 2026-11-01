cd /application1/sajjna8/rt-pzai-bplan-v1 && \
echo "BRANCH: $(git branch --show-current)" && \
find artifacts/v1.113 -maxdepth 5 -type f \
\( -name '*.pt' -o -name 'pipeline.py' -o -name 'models.py' -o -name '*params*.json' -o -name 'sanity_input.json' \) | sort
