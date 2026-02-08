@echo off
title WINDOWS DEFENDER SCAN
echo WINDOWS DEFENDER SCAN
echo ====================
powershell -Command "Start-MpScan -ScanType QuickScan"
echo.
pause
del "C:\New folder\Sunday-final-year\temp_cmd.bat" & exit
