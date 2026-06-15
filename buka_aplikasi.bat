@echo off
title Natural Reserve — Akses Terbatas
color 0A
cls

:: ============================================================
::  KONFIGURASI PASSWORD (untuk membuka .bat)
:: ============================================================
set "PASS_1=admin123"
set "PASS_2=operator2024"
set "PASS_3=supervisor99"

:: ============================================================
::  KONFIGURASI PORT
:: ============================================================
set "PORT=52741"
set "MAX_TRIES=3"
set "TRIES=0"

:HEADER
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       NATURAL RESERVE  ^|  Fish Feeding       ║
echo  ║              Akses Terbatas                  ║
echo  ╚══════════════════════════════════════════════╝
echo.

:ASK_PASSWORD
set /a TRIES+=1
if %TRIES% GTR %MAX_TRIES% goto BLOCKED
echo  Percobaan ke-%TRIES% dari %MAX_TRIES%
echo.
set /p "INPUT_PASS=  Masukkan password launcher: "
echo.

if "%INPUT_PASS%"=="%PASS_1%" goto GRANTED
if "%INPUT_PASS%"=="%PASS_2%" goto GRANTED
if "%INPUT_PASS%"=="%PASS_3%" goto GRANTED

echo  X Password salah. Silakan coba lagi.
echo.
goto ASK_PASSWORD

:GRANTED
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║          Akses Diterima - Memulai...         ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Cek Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python tidak ditemukan.
    echo  Unduh di https://python.org dan centang "Add to PATH"
    echo.
    pause
    exit /b 1
)

:: Cek file server
if not exist "%~dp0nr_server.py" (
    echo  ERROR: File nr_server.py tidak ditemukan.
    pause
    exit /b 1
)

:: Generate token
for /f "delims=" %%T in ('python -c "import secrets; print(secrets.token_hex(32))"') do set "SESSION_TOKEN=%%T"

if "%SESSION_TOKEN%"=="" (
    echo  ERROR: Gagal membuat token sesi.
    pause
    exit /b 1
)

:: Jalankan server
echo  Memulai server lokal...
start "" /min python "%~dp0nr_server.py" "%SESSION_TOKEN%" "%PORT%"
timeout /t 2 /nobreak >nul

echo  Pilih halaman yang ingin dibuka:
echo.
echo  [1] Halaman Login Pengguna
echo  [2] Halaman Admin Panel
echo.
set /p "PILIHAN=  Pilih (1/2): "

if "%PILIHAN%"=="2" (
    start "" "http://127.0.0.1:%PORT%/admin.html?t=%SESSION_TOKEN%"
) else (
    start "" "http://127.0.0.1:%PORT%/login.html?t=%SESSION_TOKEN%"
)

timeout /t 3 /nobreak >nul
echo.
echo  Aplikasi berhasil dibuka.
echo  Server berjalan di background (tutup otomatis setelah 1 jam).
echo.
timeout /t 4 /nobreak >nul
exit /b 0

:BLOCKED
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║           X  Akses Ditolak                   ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Terlalu banyak percobaan. Program ditutup.
echo.
timeout /t 4 /nobreak >nul
exit /b 1
