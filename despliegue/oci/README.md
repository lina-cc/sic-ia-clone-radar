# Despliegue en OCI (Always Free)

La app queda publicada en una máquina virtual gratuita de Oracle Cloud, siempre encendida,
con HTTPS y protegida con usuario y contraseña del equipo.

| | |
|---|---|
| Máquina | VM.Standard.A1.Flex (ARM), Ubuntu 24.04. Basta con 1 OCPU y 6 GB |
| Dirección | `https://<IP-con-guiones>.sslip.io` (dominio gratis que apunta a la IP) |
| App | servicio `fairplay` (systemd), escucha solo en `127.0.0.1:7860` |
| HTTPS | Caddy, que pide y renueva solo el certificado de Let's Encrypt |
| Datos y modelo | se descargan del dataset privado de Hugging Face la primera vez |
| Casos marcados | `/opt/fairplay/casos/casos_guardados.csv` en la VM |

## Archivos

* `instalar.sh`: instala todo (paquetes, código, entorno de Python, servicio, HTTPS y firewall). Volver a correrlo **actualiza** la app a la última versión de la rama.
* `configurar_secretos.sh`: pide el token de Hugging Face y la contraseña del equipo y los guarda en `/etc/fairplay.env` (solo root puede leerlo). **Nunca** se suben al repositorio.
* `fairplay.service`: el servicio que mantiene la app encendida y la reinicia si falla.
* `Caddyfile`: HTTPS y redirección a la app.

## Pasos (una sola vez)

1. **En la consola de OCI**, crear la instancia (Ubuntu 24.04, forma Ampere *Always Free-eligible*, IP pública) y guardar la clave privada SSH.
2. **En la subred de la instancia** → *Security Lists* → *Add Ingress Rules*: origen `0.0.0.0/0`, TCP, puertos `80,443`.
3. **En la VM** (por SSH):

   ```bash
   git clone -b feat/clasificador-pares https://github.com/sergiorebolledo/sic-ia-clone-radar.git /tmp/fp
   sudo bash /tmp/fp/despliegue/oci/configurar_secretos.sh
   bash /tmp/fp/despliegue/oci/instalar.sh
   ```

La primera vez tarda unos 10 minutos (descarga ~630 MB del modelo y arma el TF-IDF).

## Mantención

```bash
bash /opt/fairplay/repo/despliegue/oci/instalar.sh     # actualizar a la última versión
journalctl -u fairplay -f                              # ver los registros de la app
sudo systemctl restart fairplay                        # reiniciar la app
sudo bash /opt/fairplay/repo/despliegue/oci/configurar_secretos.sh   # cambiar token o contraseña
```

Para bajar los casos marcados al computador:

```bash
scp -i <clave-privada> ubuntu@<IP>:/opt/fairplay/casos/casos_guardados.csv .
```

## Cuidados

* OCI puede recuperar máquinas *Always Free* que pasan 7 días casi sin uso (CPU, red y memoria muy bajas).
* La forma A1 es gratis solo dentro del límite *Always Free*; no cambiarla a AMD o Intel.
* Si se filtra la contraseña del equipo, cambiarla con `configurar_secretos.sh`.
