@echo off
cd /d "%~dp0"
start "" http://localhost:8791
if exist venv\Scripts\python.exe (venv\Scripts\python.exe server.py) else (python server.py)
