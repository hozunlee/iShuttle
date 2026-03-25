@echo off
git commit -m "docs: finalize BE_005 ffmpeg setup" > commit_log.txt 2>&1
git push origin main >> commit_log.txt 2>&1
echo Done >> commit_log.txt
