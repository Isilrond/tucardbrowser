@echo off
:: Admin-Rechte pruefen und ggf. neu starten
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Starte als Administrator neu...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

title Tyrant Browser - Build
cd /d "%~dp0"

:: ALLE Code-Signing Variablen deaktivieren
set CSC_IDENTITY_AUTO_DISCOVERY=false
set CSC_LINK=
set WIN_CSC_LINK=
set CSC_KEY_PASSWORD=
set WIN_CSC_KEY_PASSWORD=

:: Aktuelle Version aus package.json lesen
for /f "tokens=2 delims=:," %%a in ('findstr /i "\"version\"" package.json') do (
    set CURRENT_VER=%%a
)
set CURRENT_VER=%CURRENT_VER: =%
set CURRENT_VER=%CURRENT_VER:"=%

echo.
echo  Aktuelle Version: %CURRENT_VER%
echo  Neue Version eingeben (oder Enter fuer keine Aenderung):
set /p NEW_VER=  Version: 

if not "%NEW_VER%"=="" (
    powershell -Command "(Get-Content package.json) -replace '\"version\": \"%CURRENT_VER%\"', '\"version\": \"%NEW_VER%\"' | Set-Content package.json"
    echo  Version aktualisiert: %CURRENT_VER% -^> %NEW_VER%
) else (
    echo  Version unveraendert: %CURRENT_VER%
)
echo.

:: dist-Ordner leeren
if exist dist\ (
    echo Loesche alten dist-Ordner...
    rmdir /s /q dist
)

echo npm install...
call npm install --save-dev electron electron-builder
if errorlevel 1 (echo FEHLER bei npm install && pause && exit /b 1)

echo.
echo Baue Anwendung...
call npx electron-builder --win --x64
if errorlevel 1 (echo FEHLER beim Build && pause && exit /b 1)

:: Bilder-Check
echo.
echo Bilder in win-unpacked\resources\images:
dir /b dist\win-unpacked\resources\images\*.jpg 2>nul | find /c ".jpg"

:: win-unpacked loeschen
if exist dist\win-unpacked\ (
    echo Loesche temporaeren win-unpacked Ordner...
    rmdir /s /q dist\win-unpacked
)

echo.
echo ===========================
echo  Fertig! Ausgabe in dist\
echo ===========================
dir dist\
echo.
pause
