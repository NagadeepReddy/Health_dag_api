git diff --check
Select-String -Path .\src\main\java\com\verizon\jarvis\repository\SessionRepository.java -Pattern '"CREATED_DATE"' -Context 2,3
