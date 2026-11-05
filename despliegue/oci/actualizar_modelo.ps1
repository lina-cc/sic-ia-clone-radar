# Hace que el servidor descargue el último modelo del dataset de Hugging Face y reinicie la app.
# Antes: correr el notebook en Colab y subir la carpeta modelo/ nueva al dataset.
# Uso:  .\actualizar_modelo.ps1 -Ip 1.2.3.4 [-Clave C:\ruta\clave.key]
param(
    [Parameter(Mandatory = $true)][string]$Ip,
    [string]$Clave = "$HOME\.ssh\oci_fairplay.key"
)
ssh -o ServerAliveInterval=20 -i $Clave "ubuntu@$Ip" "bash /opt/fairplay/repo/despliegue/oci/actualizar_modelo.sh"
if ($LASTEXITCODE -ne 0) { Write-Host "La actualización falló; la app sigue con el modelo anterior." -ForegroundColor Red }
