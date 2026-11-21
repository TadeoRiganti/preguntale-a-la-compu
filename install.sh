#!/usr/bin/env bash
set -e

echo "📦 Instalando dependencias del sistema (espeak-ng y portaudio)..."
sudo apt-get update && sudo apt-get install -y espeak-ng libportaudio2 curl

if ! command -v uv &> /dev/null; then
    echo "⚡ Instalando uv..."
    curl -LsSf https://astral.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "🐍 Instalando comando global 'consultar-computadora'..."
uv tool install --force .

echo "✅ ¡Listo! Asegúrate de tener Ollama instalado con el modelo gemma4:e4b."
echo "   Para iniciar, ejecuta: consultar-computadora"
