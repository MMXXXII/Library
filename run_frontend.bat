@echo off
cd /d C:\deploy\frontend
python -m http.server 4173 > frontend.log 2>&1