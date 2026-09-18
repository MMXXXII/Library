@echo off
cd /d C:\deploy\library-app\frontend
pythonw -m http.server 4173 > ..\frontend.log 2>&1