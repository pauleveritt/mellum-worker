@echo off
setlocal

rem llama.cpp learned Mellum's architecture in build 9482.
set "MIN_BUILD=9482"
set "LLAMA_ID=ggml.llamacpp"
rem This repo and Pi need Node.js 24 or newer; npm comes with it.
set "MIN_NODE=24"
set "PI_PACKAGE=@earendil-works/pi-coding-agent"

call :ensure uv.exe astral-sh.uv
if errorlevel 1 exit /b 1

call :ensure llama-server.exe %LLAMA_ID%
if errorlevel 1 exit /b 1

call :check_llama
if errorlevel 1 exit /b 1

call :ensure node.exe OpenJS.NodeJS.LTS
if errorlevel 1 exit /b 1

call :check_node
if errorlevel 1 exit /b 1

call :ensure_pi
if errorlevel 1 exit /b 1

echo.
echo All checks completed successfully.
echo If anything was installed, open a new terminal before using it.
exit /b 0

:ensure
where /q "%~1"
if not errorlevel 1 (
    echo [OK] %~1 is already available.
    exit /b 0
)

echo [MISSING] %~1 was not found on PATH.

where /q winget.exe
if errorlevel 1 (
    echo [ERROR] WinGet is required to install %~1.
    echo Install App Installer from the Microsoft Store, then rerun.
    exit /b 1
)

echo Installing %~2...
winget install --id "%~2" --exact --source winget --accept-package-agreements --accept-source-agreements
rem WinGet reports failures as negative codes, which "if errorlevel 1" misses.
if %errorlevel% neq 0 (
    echo [ERROR] Installation of %~2 failed.
    echo Review the WinGet message above.
    exit /b 1
)

echo [OK] Installation of %~2 completed.
exit /b 0

rem Node.js must be new enough for this repo and Pi; npm comes with it.
:check_node
rem A fresh WinGet install is on PATH only in a new terminal, and is current.
where /q node.exe
if errorlevel 1 exit /b 0
set "NODE_MAJOR="
for /f "tokens=1 delims=v." %%V in ('node --version') do set "NODE_MAJOR=%%V"
if not defined NODE_MAJOR (
    echo [WARN] Could not read the Node.js version; this repo needs %MIN_NODE% or newer.
    exit /b 0
)
if %NODE_MAJOR% geq %MIN_NODE% (
    echo [OK] Node.js %NODE_MAJOR% is new enough.
    exit /b 0
)
echo [OLD] Node.js %NODE_MAJOR% is too old; this repo and Pi need %MIN_NODE% or newer.
echo Upgrade it, for example: winget install --id OpenJS.NodeJS.LTS --exact --source winget
echo Then open a new terminal and rerun this script.
exit /b 1

rem Pi is an npm package; npm is a batch file, so it must be run with "call".
:ensure_pi
where /q pi.cmd
if not errorlevel 1 (
    echo [OK] pi is already available.
    exit /b 0
)
echo [MISSING] pi was not found on PATH.
where /q npm.cmd
if errorlevel 1 (
    echo [ACTION] Node.js was just installed; open a new terminal and rerun to install Pi.
    exit /b 1
)
echo Installing %PI_PACKAGE%...
call npm install -g %PI_PACKAGE%
if %errorlevel% neq 0 (
    echo [ERROR] Installation of %PI_PACKAGE% failed.
    echo Review the npm message above.
    exit /b 1
)
where /q pi.cmd
if errorlevel 1 (
    echo [OK] Installed %PI_PACKAGE%. Open a new terminal before running pi.
    exit /b 0
)
echo [OK] Installation of %PI_PACKAGE% completed.
exit /b 0

rem Every llama-server on PATH must be new enough, or an old one that comes
rem first wins and cannot load Mellum. WinGet's copy is upgraded in place;
rem any other old copy is renamed to .old once a current build is installed.
:check_llama
rem A fresh WinGet install is on PATH only in a new terminal, and is current.
where /q llama-server.exe
if errorlevel 1 exit /b 0

echo llama-server on PATH, in the order Windows tries them:
set "FIRST_BUILD="
set "HAVE_GOOD="
set "OLD_WINGET="
set "OLD_OTHER="
for /f "delims=" %%P in ('where llama-server.exe') do call :consider "%%P"

if not defined FIRST_BUILD (
    echo [WARN] Could not read the build of the first llama-server.
    echo Mellum needs llama.cpp build %MIN_BUILD% or newer; check: llama-server --version
    exit /b 0
)
if not defined OLD_WINGET if not defined OLD_OTHER (
    echo [OK] Every llama-server on PATH supports Mellum.
    exit /b 0
)

rem Install or upgrade WinGet's copy unless a current build is already on PATH.
set "NEED_WINGET=%OLD_WINGET%"
if not defined HAVE_GOOD set "NEED_WINGET=1"
if defined NEED_WINGET (
    call :winget_llama
    if errorlevel 1 exit /b 1
)

if defined OLD_OTHER (
    set "RETIRE_FAILED="
    for /f "delims=" %%P in ('where llama-server.exe') do call :retire "%%P"
)
if defined RETIRE_FAILED exit /b 1

echo [OK] llama-server is fixed. Open a new terminal, then check: llama-server --version
exit /b 0

rem List one llama-server and note whether it is old, and whether it is WinGet's.
:consider
call :build_of "%~1"
if "%BUILD%"=="" (
    echo   %~1  [build unknown]
    exit /b 0
)
if not defined FIRST_BUILD set "FIRST_BUILD=%BUILD%"
if %BUILD% geq %MIN_BUILD% (
    echo   %~1  [build %BUILD%, OK]
    set "HAVE_GOOD=1"
    exit /b 0
)
echo   %~1  [build %BUILD%, too old]
echo "%~1" | findstr /i /c:"\WinGet\" >nul
if errorlevel 1 (set "OLD_OTHER=1") else (set "OLD_WINGET=1")
exit /b 0

rem Newer builds print "version: 0.7.0-dev (build 11829, ...)", older ones "version: 7360 (...)".
:build_of
set "BUILD="
for /f %%B in ('powershell -NoProfile -Command "$o = (& '%~1' --version 2>&1 | Out-String); if ($o -match '\(build (\d+)') { $matches[1] } elseif ($o -match 'version: (\d+) \(') { $matches[1] }"') do set "BUILD=%%B"
exit /b 0

:winget_llama
where /q winget.exe
if errorlevel 1 (
    echo [ERROR] WinGet is required to install a current llama.cpp.
    echo Install App Installer from the Microsoft Store, then rerun.
    exit /b 1
)
winget list --id %LLAMA_ID% --exact --source winget >nul 2>&1
if %errorlevel% neq 0 goto :winget_install
echo Upgrading %LLAMA_ID%...
winget upgrade --id %LLAMA_ID% --exact --source winget --accept-package-agreements --accept-source-agreements
rem -1978335189: no newer version, so WinGet's copy is already current.
if %errorlevel% neq 0 if %errorlevel% neq -1978335189 goto :winget_failed
exit /b 0

:winget_install
echo Installing %LLAMA_ID%...
winget install --id %LLAMA_ID% --exact --source winget --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 goto :winget_failed
exit /b 0

:winget_failed
echo [ERROR] WinGet could not install or upgrade %LLAMA_ID%.
echo Review the WinGet message above.
exit /b 1

rem Rename an old llama-server that is not WinGet's, so it stops shadowing the current one.
:retire
echo "%~1" | findstr /i /c:"\WinGet\" >nul
if not errorlevel 1 exit /b 0
call :build_of "%~1"
if "%BUILD%"=="" exit /b 0
if %BUILD% geq %MIN_BUILD% exit /b 0
move /y "%~1" "%~1.old" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Could not rename %~1 ^(build %BUILD%^).
    echo Rename or delete it yourself, or remove %~dp1 from PATH, then rerun.
    set "RETIRE_FAILED=1"
    exit /b 0
)
echo [FIXED] Renamed %~1 to %~nx1.old ^(build %BUILD%, too old for Mellum^).
echo         Undo: move "%~1.old" "%~1"
exit /b 0
