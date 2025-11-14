@echo off
REM Simple batch file to backup Salsa2 database from VM to Windows
REM Save as: backup_salsa2.bat

setlocal enabledelayedexpansion

REM Configuration
set VM_USER=lior
set VM_HOST=192.168.10.52
set VM_DB_PATH=/home/lior/Salsa2Simulator/salsa2.db
set ONEDRIVE_BACKUP_PATH=C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup

REM Get timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

set BACKUP_FILE=salsa2_%timestamp%.db

echo ========================================
echo Salsa2 Database Backup from VM
echo ========================================
echo VM: %VM_USER%@%VM_HOST%
echo Source: %VM_DB_PATH%
echo Destination: %ONEDRIVE_BACKUP_PATH%\%BACKUP_FILE%
echo.

REM Create backup directory if needed
if not exist "%ONEDRIVE_BACKUP_PATH%" (
    mkdir "%ONEDRIVE_BACKUP_PATH%"
    echo Created backup directory
)

REM Copy database using SCP
echo Copying database from VM...
scp %VM_USER%@%VM_HOST%:%VM_DB_PATH% "%ONEDRIVE_BACKUP_PATH%\%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo.
    echo ✓ Backup completed successfully!
    echo ✓ File: %BACKUP_FILE%
    
    REM Show file size
    for %%A in ("%ONEDRIVE_BACKUP_PATH%\%BACKUP_FILE%") do (
        set size=%%~zA
        set /a size_mb=!size! / 1048576
        echo ✓ Size: !size_mb! MB
    )
    
    echo.
    echo Recent backups:
    dir /b /o-d "%ONEDRIVE_BACKUP_PATH%\salsa2_*.db" 2>nul | findstr /n "^" | findstr "^[1-5]:"
    
) else (
    echo.
    echo ✗ Backup failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Backup completed at %date% %time%
echo ========================================
pause
