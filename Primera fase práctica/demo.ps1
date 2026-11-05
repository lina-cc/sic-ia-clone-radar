# Abre la app de FairPlay AI con un enlace público temporal (Windows / PowerShell).
#
# Uso, desde la carpeta "Primera fase práctica":
#     .\demo.ps1                      # con el modelo en modelo\ (copiado del notebook)
#     .\demo.ps1 -Dataset usuario/fairplay-datos
#                                     # descarga el modelo desde el dataset privado de Hugging Face
#                                     # (antes: iniciar sesión con "hf auth login")
#
# La primera vez crea el entorno .venv con Python 3.12 e instala las dependencias (unos minutos).
# Gradio imprime un enlace https://....gradio.live que funciona mientras esta ventana siga abierta
# (hasta una semana). Para cerrar la app: Ctrl+C.
param(
    [string]$Dataset = "",
    [int]$Puerto = 7860
)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    # Usa el primer Python que funcione, de 3.12 en adelante (con el que se probó la app)
    $version = $null
    foreach ($v in "3.12", "3.13", "3.14") {
        py "-$v" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $version = $v; break }
    }
    if (-not $version) {
        throw "No se encontró Python 3.12 o superior. Instálalo desde python.org y vuelve a intentar."
    }
    Write-Host "Creando el entorno .venv con Python $version (solo la primera vez, tarda unos minutos)..."
    py "-$version" -m venv .venv
    if (-not (Test-Path $python)) { throw "No se pudo crear el entorno .venv con $base" }
    & $python -m pip install --upgrade pip --quiet
    & $python -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Recurse -Force .venv   # para que el próximo intento parta de cero
        throw "Falló la instalación de dependencias (revisa tu conexión y vuelve a ejecutar demo.ps1)."
    }
}

if ($Dataset) {
    $env:FAIRPLAY_HF_DATASET = $Dataset
} elseif (-not (Test-Path "modelo\modelo_pares.joblib")) {
    Write-Host "Aviso: no hay modelo en modelo\ y no se indicó -Dataset. Se abrirá solo la línea base TF-IDF."
}

& $python -W ignore app.py --share --puerto $Puerto
