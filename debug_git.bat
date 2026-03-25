@echo off
echo --- Git Status --- > debug_git.txt
git status >> debug_git.txt 2>&1
echo --- SSH Verification --- >> debug_git.txt
ssh -T -o BatchMode=yes git@github.com >> debug_git.txt 2>&1
echo --- Git Push Dry Run --- >> debug_git.txt
git push --dry-run >> debug_git.txt 2>&1
echo --- Done --- >> debug_git.txt
