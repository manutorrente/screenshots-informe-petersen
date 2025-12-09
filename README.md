# Kibana Screenshots

Script automatizado para tomar capturas de pantalla de dashboards de Kibana y Cloudera usando Playwright.

## Requisitos Previos

- Python 3.8 o superior
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes Python ultrarrápido

## Instalación

### 1. Instalar uv (si no lo tienes)

```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Sincronizar dependencias

```powershell
uv sync
```

Este comando instalará todas las dependencias del proyecto definidas en `pyproject.toml`.

### 3. Instalar navegadores de Playwright

```powershell
uv run playwright install
```

Este comando descarga e instala los navegadores necesarios (Chromium, Firefox, WebKit) para Playwright.

## Configuración

### 1. Crear archivo `.env`

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Credenciales de Elastic/Kibana
ELASTIC_USER=elastic
ELASTIC_PASSWORD=tu_password_de_elastic

# Credenciales de Cloudera
CLOUDERA_USER=tu_usuario_cloudera
CLOUDERA_PASSWORD=tu_password_cloudera
```

### 2. Verificar URLs

Verifica que las URLs de los dashboards en los scripts sean correctas según tu entorno.

## Ejecución

Para ejecutar el script principal que toma todas las capturas:

```powershell
uv run .\main.py
```

Este script:
- Limpia el directorio `output/` de capturas anteriores
- Ejecuta las capturas de Cloudera
- Ejecuta las capturas de Kibana
- Guarda todas las imágenes en el directorio `output/`

## Estructura del Proyecto

```
.
├── main.py                    # Script principal
├── screenshots_kibana.py      # Script para capturas de Kibana
├── screenshots_cloudera.py    # Script para capturas de Cloudera
├── output/                    # Directorio de salida de capturas
├── pyproject.toml            # Configuración de dependencias
└── .env                      # Variables de entorno (credenciales)
```

## Solución de Problemas

### Error: "playwright not found"
Ejecuta: `uv run playwright install`

### Error: "No module named 'playwright'"
Ejecuta: `uv sync`

### Las capturas salen en blanco
- Verifica las credenciales en el archivo `.env`
- Asegúrate de que las URLs sean accesibles
- Aumenta los tiempos de espera en los scripts si la conexión es lenta

## Notas

- El script usa `headless=False` por defecto para poder ver el proceso
- Las capturas se toman con zoom de 150% para mejor claridad
- El script espera a que los elementos se carguen completamente antes de capturar
