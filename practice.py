GIT_PAGER=cat git diff --cached --check && \
GIT_PAGER=cat git diff --cached --stat && \
echo "STAGED FILE COUNT:" && \
git diff --cached --name-only | wc -l
