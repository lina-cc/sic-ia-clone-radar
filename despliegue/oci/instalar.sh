#!/usr/bin/env bash
# Instala FairPlay AI en una VM Ubuntu 24.04 de OCI (Always Free, ARM o x86).
# Uso, dentro de la VM:  bash instalar.sh [rama]
# Se puede volver a correr para actualizar: baja los últimos cambios y reinicia la app.
set -euo pipefail

REPO="${FAIRPLAY_REPO:-https://github.com/sergiorebolledo/sic-ia-clone-radar.git}"
RAMA="${1:-feat/clasificador-pares}"
BASE=/opt/fairplay
IP=$(curl -s https://ifconfig.me || hostname -I | awk '{print $1}')
DOMINIO="${FAIRPLAY_DOMINIO:-${IP//./-}.sslip.io}"   # dominio gratis que apunta a la IP pública

echo "==> Paquetes del sistema"
sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q python3-venv python3-pip git caddy iptables-persistent

echo "==> Memoria de intercambio (4 GB), por si el TF-IDF necesita más RAM al arrancar"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> Código ($RAMA)"
sudo mkdir -p "$BASE" && sudo chown "$USER:$USER" "$BASE"
if [ -d "$BASE/repo/.git" ]; then
  git -C "$BASE/repo" fetch -q origin "$RAMA" && git -C "$BASE/repo" checkout -q "$RAMA" && git -C "$BASE/repo" reset -q --hard "origin/$RAMA"
else
  git clone -q -b "$RAMA" "$REPO" "$BASE/repo"
fi
ln -sfn "$BASE/repo/Primera fase práctica" "$BASE/app"   # ruta sin espacios para systemd

echo "==> Entorno de Python"
[ -d "$BASE/venv" ] || python3 -m venv "$BASE/venv"
"$BASE/venv/bin/pip" install -q --upgrade pip
"$BASE/venv/bin/pip" install -q -r "$BASE/app/requirements.txt"

echo "==> Servicio de la app"
sed "s/__USUARIO__/$USER/" "$BASE/repo/despliegue/oci/fairplay.service" | sudo tee /etc/systemd/system/fairplay.service >/dev/null
[ -f /etc/fairplay.env ] || { echo "Falta /etc/fairplay.env: corre primero configurar_secretos.sh"; exit 1; }
sudo systemctl daemon-reload
sudo systemctl enable -q fairplay
sudo systemctl restart fairplay

echo "==> HTTPS con Caddy en https://$DOMINIO"
sed "s/__DOMINIO__/$DOMINIO/" "$BASE/repo/despliegue/oci/Caddyfile" | sudo tee /etc/caddy/Caddyfile >/dev/null
sudo systemctl reload caddy || sudo systemctl restart caddy

echo "==> Firewall de Ubuntu: abrir 80 y 443 (las imágenes de OCI solo dejan pasar SSH)"
for p in 80 443; do
  sudo iptables -C INPUT -p tcp --dport $p -j ACCEPT 2>/dev/null || \
    sudo iptables -I INPUT 5 -m state --state NEW -p tcp --dport $p -j ACCEPT
done
sudo netfilter-persistent save >/dev/null

echo
echo "Listo. La app tarda unos minutos en descargar el modelo la primera vez."
echo "Ver el avance:  journalctl -u fairplay -f"
echo "Dirección:      https://$DOMINIO"
