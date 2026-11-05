#!/usr/bin/env bash
# Corre en la VM. Descarga el modelo más reciente del dataset de Hugging Face y reinicia la app.
# Si el modelo nuevo no carga, vuelve al anterior.
set -euo pipefail
APP=/opt/fairplay/app
MODELO="$APP/modelo"
RESPALDO="$APP/modelo.anterior"

echo "==> Respaldando el modelo actual"
rm -rf "$RESPALDO"
[ -d "$MODELO" ] && mv "$MODELO" "$RESPALDO"
rm -rf "$APP/.cache/huggingface/download/modelo"   # olvidar las descargas anteriores

echo "==> Reiniciando la app (descarga ~630 MB, tarda unos minutos)"
desde=$(date '+%Y-%m-%d %H:%M:%S')
sudo systemctl restart fairplay
for i in $(seq 1 120); do
  log=$(journalctl -u fairplay --since "$desde" --no-pager -o cat)
  if grep -q "Running on" <<<"$log"; then break; fi
  sleep 5
done

if grep -q "Modelo listo" <<<"$log" && ! grep -q "quedará desactivada" <<<"$log"; then
  grep -E "Modelo listo|Descargando" <<<"$log" | tail -3
  usa_B=$(cd "$APP" && /opt/fairplay/venv/bin/python -c "import joblib;print('B' if joblib.load('modelo/modelo_pares.joblib').get('modelo_B') is not None else 'A')")
  echo "Listo: la app usa el Modelo $usa_B."
else
  echo "El modelo nuevo no cargó. Últimos registros:"; tail -15 <<<"$log"
  if [ -d "$RESPALDO" ]; then
    echo "==> Volviendo al modelo anterior"
    rm -rf "$MODELO" && mv "$RESPALDO" "$MODELO" && sudo systemctl restart fairplay
  fi
  exit 1
fi
