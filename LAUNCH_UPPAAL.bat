@echo off
rem Opens the UPPAAL GUI on the 1M1S demo model.
rem UPPAAL is looked for in this order:
rem   1. the folder written in uppaal_path.txt (absolute, or relative to this project folder)
rem   2. a folder named "uppaal" inside this project folder
rem UPPAAL 5.0 needs Java 11-21. If a Temurin JDK 21 is installed, it is used directly.
setlocal
set "HERE=%~dp0"
set "UPPAAL_DIR="
if exist "%HERE%uppaal_path.txt" set /p UPPAAL_DIR=<"%HERE%uppaal_path.txt"
if not "%UPPAAL_DIR%"=="" if not exist "%UPPAAL_DIR%\uppaal.jar" if exist "%HERE%%UPPAAL_DIR%\uppaal.jar" set "UPPAAL_DIR=%HERE%%UPPAAL_DIR%"
if not "%UPPAAL_DIR%"=="" if not exist "%UPPAAL_DIR%\uppaal.jar" set "UPPAAL_DIR="
if "%UPPAAL_DIR%"=="" if exist "%HERE%uppaal\uppaal.jar" set "UPPAAL_DIR=%HERE%uppaal"
if "%UPPAAL_DIR%"=="" (
  echo UPPAAL not found.
  echo Write your UPPAAL folder ^(the one containing uppaal.jar^) into uppaal_path.txt,
  echo or unzip UPPAAL into a folder named "uppaal" inside this project folder.
  pause
  exit /b 1
)
set "MODEL=%HERE%model\demo_view\amba_AHB_1M1S_clean.uppaal.xml"

set "JAVA21="
for /d %%D in ("%ProgramFiles%\Eclipse Adoptium\jdk-21*") do if exist "%%D\bin\javaw.exe" set "JAVA21=%%D\bin\javaw.exe"
if not "%JAVA21%"=="" (
  start "" "%JAVA21%" -jar "%UPPAAL_DIR%\uppaal.jar" "%MODEL%"
  exit /b 0
)
if exist "%UPPAAL_DIR%\uppaal.exe" (
  start "" "%UPPAAL_DIR%\uppaal.exe" "%MODEL%"
) else (
  start "" javaw -jar "%UPPAAL_DIR%\uppaal.jar" "%MODEL%"
)
