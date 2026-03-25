@echo off
echo Testing SSH Connection... > git_test_log.txt
ssh -T -o BatchMode=yes git@github.com >> git_test_log.txt 2>&1
echo Testing Git Remote... >> git_test_log.txt
git ls-remote origin 2>&1 >> git_test_log.txt
echo Done. >> git_test_log.txt
