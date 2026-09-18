@echo off
cd /d C:\deploy\library-app
python manage.py runserver 0.0.0.0:8000 > backend.log 2>&1