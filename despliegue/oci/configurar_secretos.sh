#!/usr/bin/env bash
# Guarda en la VM los datos privados de la app, sin que queden en el repo ni en el historial.
# Uso:  sudo bash configurar_secretos.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Córrelo con sudo."; exit 1; }

read -rp  "Dataset de Hugging Face [Reboll/fairplay-datos]: " DATASET
read -rsp "Token de lectura de Hugging Face (no se muestra): " TOKEN; echo
read -rp  "Usuario para entrar a la app [fairplay]: " USUARIO
read -rsp "Contraseña del equipo para entrar a la app (no se muestra): " CLAVE; echo
[ -n "$TOKEN" ] && [ -n "$CLAVE" ] || { echo "El token y la contraseña son obligatorios."; exit 1; }

umask 077
cat > /etc/fairplay.env <<FIN
FAIRPLAY_HF_DATASET=${DATASET:-Reboll/fairplay-datos}
HF_TOKEN=$TOKEN
FAIRPLAY_USUARIO=${USUARIO:-fairplay}
FAIRPLAY_CLAVE=$CLAVE
GRADIO_SERVER_NAME=127.0.0.1
GRADIO_SERVER_PORT=7860
GRADIO_ANALYTICS_ENABLED=False
FIN
chmod 600 /etc/fairplay.env
echo "Guardado en /etc/fairplay.env (solo root puede leerlo)."
systemctl is-enabled -q fairplay 2>/dev/null && systemctl restart fairplay && echo "App reiniciada con los nuevos datos." || true
