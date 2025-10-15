@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no PATH.
    echo Instale o Python ou adicione-o ao PATH e tente novamente.
    echo.
    pause
    exit /b 1
)

echo Iniciando processo de compilacao...
python build.py
set "exit_code=%errorlevel%"

echo.
if %exit_code% neq 0 (
    echo A compilacao falhou com o codigo %exit_code%.
    echo Verifique as mensagens acima para mais detalhes.
    pause
    exit /b %exit_code%
)

echo Compilacao concluida com sucesso!
pause
exit /b 0
