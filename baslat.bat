@echo off
color 0B
echo Sanal ortam (venv) baslatiliyor...
call .\.venv\Scripts\activate.bat

echo.
echo Icerik ve Veri Yonetim Paneli aciliyor...
python GUI.py

pause