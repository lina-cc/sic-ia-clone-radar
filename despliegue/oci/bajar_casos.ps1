# Baja al computador los casos que el equipo marcó en la app del servidor.
# Uso:  .\bajar_casos.ps1 -Ip 1.2.3.4 [-Clave C:\ruta\clave.key] [-Destino carpeta]
# Después, subir el archivo a Drive como MyDrive/fairplay/data/casos_guardados.csv
param(
    [Parameter(Mandatory = $true)][string]$Ip,
    [string]$Clave = "$HOME\.ssh\oci_fairplay.key",
    [string]$Destino = ".\casos"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $Destino | Out-Null
$fecha = Get-Date -Format "yyyy-MM-dd_HHmm"
$archivo = Join-Path $Destino "casos_guardados_$fecha.csv"
scp -q -i $Clave "ubuntu@${Ip}:/opt/fairplay/casos/casos_guardados.csv" $archivo
if ($LASTEXITCODE -ne 0) { throw "No se pudo bajar el archivo. ¿Ya se marcó algún caso en la app?" }
$filas = (Import-Csv $archivo).Count
Write-Host "Listo: $filas casos en $archivo"
Write-Host "Súbelo a Drive como MyDrive/fairplay/data/casos_guardados.csv (reemplazando el anterior)."
