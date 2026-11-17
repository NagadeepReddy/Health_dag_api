curl -sS -o /dev/null -w 'HTTP %{http_code}\n' --max-time 15 \
'https://oneartifactoryci.verizon.com/artifactory/ienv-vcg-jarvis-maven-virtual/'
