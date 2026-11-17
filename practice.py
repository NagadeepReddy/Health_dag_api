cat > /application1/sajjna8/redis_latency_test/maven-settings-public.xml <<'EOF'
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0">
  <mirrors>
    <mirror>
      <id>verizon-artifactory</id>
      <mirrorOf>*</mirrorOf>
      <url>https://oneartifactoryci.verizon.com/artifactory/ienv-vcg-jarvis-maven-virtual/</url>
    </mirror>
  </mirrors>
</settings>
EOF

echo READY
