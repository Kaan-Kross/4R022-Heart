@echo off
REM 4R022 Heart - Windows one-click build  (no Python needed)
REM Windows tek tikla build  (Python gerekmez)
REM Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License
setlocal
title 4R022 Heart - Windows Build
echo.
echo  4R022 Heart - automatic build / otomatik build
echo  Python is NOT required; everything is set up for you. / Python gerekmez, her sey otomatik kurulur.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_windows.ps1" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo  BUILD FAILED / BUILD BASARISIZ  ^(code %RC%^)
) else (
  echo  Build finished. See the "Release" folder. / Build tamam, "Release" klasorune bakin.
)
if /I not "%CI%"=="true" pause
exit /b %RC%
