@echo off
cd /d c:\Users\dhiresh\OneDrive\Desktop\bot_3
set MONGO_URI=
echo Starting mini app server...
.venv\Scripts\python.exe -m flask --app app.mini_app run --port 5000 > server_log.txt 2>&1
echo Server stopped.

