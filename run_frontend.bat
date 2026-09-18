@echo off
cd /d C:\deploy\library-app\frontend
python -m http.server 4173 > ..\frontend.log 2>&1