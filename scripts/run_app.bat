@echo off
rem ============================================================================
rem  LibranzaRadar - abre la app en local con doble clic.
rem  1. Si la app ya esta corriendo, solo abre el navegador.
rem  2. Si no existe el entorno .venv, lo crea con uv e instala requirements.txt.
rem  3. Revisa que esten models\model.joblib y models\input_schema.json.
rem  4. Arranca Streamlit en http://localhost:8501 y abre el navegador.
rem  Para detener la app: Ctrl+C en esta ventana (o cerrarla).
rem ============================================================================
chcp 65001 >nul
setlocal
title LibranzaRadar - app en local
cd /d "%~dp0.."

set "PORT=8501"
set "URL=http://localhost:%PORT%"

echo.
echo  ==============================================
echo    LibranzaRadar - abriendo la app en local
echo  ==============================================
echo.

rem --- 1. ¿Ya está corriendo? -------------------------------------------------
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if %errorlevel%==0 (
    echo  La app ya esta corriendo. Abriendo %URL% en el navegador...
    start "" "%URL%"
    ping -n 5 127.0.0.1 >nul
    exit /b 0
)

rem --- 2. Entorno de Python ---------------------------------------------------
if exist ".venv\Scripts\python.exe" goto entorno_ok
echo  No encuentro el entorno .venv. Lo voy a crear con uv - tarda unos minutos.
where uv >nul 2>nul
if errorlevel 1 (
    echo  ERROR: no esta instalado uv. Instalelo con: winget install astral-sh.uv
    echo  y vuelva a abrir este archivo.
    goto error
)
uv venv --python 3.12 .venv
if errorlevel 1 goto error
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
if errorlevel 1 goto error
:entorno_ok
echo  [ok] Entorno de Python encontrado.

rem --- 3. Archivos del modelo -------------------------------------------------
if not exist "models\model.joblib" (
    echo  ERROR: falta models\model.joblib. Haga git pull o ejecute el notebook 09.
    goto error
)
if not exist "models\input_schema.json" (
    echo  ERROR: falta models\input_schema.json. Haga git pull o ejecute el notebook 09.
    goto error
)
echo  [ok] Modelo y esquema encontrados.

rem --- 4. Arrancar la app -----------------------------------------------------
set "PYTHONUTF8=1"
echo.
echo  Arrancando la app en %URL% ...
echo  El navegador se abre en unos segundos.
echo  NO CIERRE ESTA VENTANA mientras use la app.
echo  Para detenerla: Ctrl+C y luego S.
echo.
rem Abre el navegador cuando el servidor ya tuvo tiempo de arrancar (ping = esperar ~6 s)
start "" /min cmd /c "ping -n 7 127.0.0.1 >nul & start "" %URL%"
rem headless evita que Streamlit pida un correo la primera vez; address=localhost: solo este computador puede abrir la app
".venv\Scripts\python.exe" -m streamlit run app\streamlit_app.py --server.port %PORT% --server.address localhost --server.headless true --browser.gatherUsageStats false
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo  Algo fallo. Lea el mensaje de arriba; la solucion a los errores comunes esta en el README.
pause
exit /b 1
