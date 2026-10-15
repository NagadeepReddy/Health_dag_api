git diff --cached --check && \
echo "CURRENT BRANCH:" && git branch --show-current && \
echo "CONFIGURED REMOTES:" && git remote && \
echo "STAGED FILE COUNT:" && git diff --cached --name-only | wc -l && \
echo "TRACKED CHANGES:" && git status --short --untracked-files=no
