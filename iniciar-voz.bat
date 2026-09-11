@echo off
title Mobs Falantes - Servidor de Voz
cd /d "%~dp0"
set PYTHONUTF8=1

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente Python pela primeira vez...
    python -m venv .venv || goto erro
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto erro
)

echo Iniciando servidor de voz em http://127.0.0.1:5005
echo (a primeira execucao baixa o Whisper e as vozes, pode demorar alguns minutos)
".venv\Scripts\python.exe" server.py %*
pause
exit /b

:erro
echo Algo deu errado ao preparar o ambiente Python.
pause
