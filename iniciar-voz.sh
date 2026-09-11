#!/usr/bin/env sh
# Servidor de voz do Mobs Falantes (Linux/macOS). No Windows use iniciar-voz.bat.
cd "$(dirname "$0")" || exit 1
export PYTHONUTF8=1

if [ ! -x .venv/bin/python ]; then
    echo "Criando ambiente Python pela primeira vez..."
    python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt || exit 1
fi

echo "Iniciando servidor de voz em http://127.0.0.1:5005"
echo "(a primeira execucao baixa o Whisper e as vozes, pode demorar alguns minutos)"
exec .venv/bin/python server.py "$@"
