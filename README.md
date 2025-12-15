# 🚀 API Consulta RUC SUNAT

API REST completa y script CLI para consultar información de RUC en la página de SUNAT usando web scraping con Selenium. Incluye soporte para procesamiento en lote con threading, Docker, y extracción de datos extendidos.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
  - [Opción 1: Instalación Local](#opción-1-instalación-local)
  - [Opción 2: Docker (Recomendado)](#opción-2-docker-recomendado)
- [Configuración](#-configuración)
- [Uso](#-uso)
  - [API REST (FastAPI)](#1-api-rest-fastapi)
  - [Línea de Comandos (CLI)](#2-línea-de-comandos-cli)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Datos que Extrae](#-datos-que-extrae)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Troubleshooting](#-troubleshooting)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)

---

## Características

- **API REST** con FastAPI y documentación interactiva (Swagger/ReDoc)
- **CLI ** con múltiples opciones de consulta
- **Consultas en lote** con soporte de threading para procesar múltiples RUCs en paralelo
- **Dockerizado** para despliegue rápido y consistente
- **Extracción completa** de información básica y extendida
- **Modo headless** para ejecución sin interfaz gráfica
- **Validación de datos** con Pydantic
- **Manejo de errores** robusto con screenshots de depuración

---

## Estructura del Proyecto

```
webscraping-sunat/
├── api.py                    # API REST con FastAPI
├── scraper.py                # Clase SUNATScraper para web scraping
├── cli.py                    # Script de línea de comandos (CLI)
├── app.py                    # Script original (deprecated, usar cli.py)
├── requirements.txt          # Dependencias del proyecto
├── Dockerfile                # Configuración de Docker
├── docker-compose.yml        # Orquestación de contenedores
├── .dockerignore             # Archivos ignorados por Docker
├── .env.example              # Ejemplo de variables de entorno
├── .env                      # Variables de entorno (crear manualmente)
└── README.md                 # Este archivo
```

---

## Instalación

### Opción 1: Instalación Local

**Requisitos previos:**
- Python 3.11+
- Google Chrome instalado
- pip

**Pasos:**

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd webscraping-sunat
```

2. **Crear entorno virtual (recomendado):**
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Ejecutar:**
```bash
# API
uvicorn api:app --reload

# CLI
python cli.py 20267367146
```

---

### Opción 2: Docker (Recomendado)

**Requisitos previos:**
- Docker
- Docker Compose

**Pasos:**

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd webscraping-sunat
```

2. **Crear archivo `.env` (opcional):**
```bash
cp .env.example .env
```

Editar `.env` si deseas cambiar el puerto:
```env
HOST=0.0.0.0
PORT=8000
```

3. **Construir y ejecutar con Docker Compose:**
```bash
# Iniciar el servicio
docker compose up --build

# O en modo detached (segundo plano)
docker compose up -d --build
```

4. **Verificar que está corriendo:**
```bash
curl http://localhost:8000/health
```

5. **Detener el servicio:**
```bash
docker compose down
```

**Características de Docker:**
- Imagen base Python 3.11-slim
- Google Chrome instalado automáticamente
- Volumen montado para desarrollo en vivo
- Puerto configurable via variables de entorno
- Red bridge personalizada
- Shared memory de 2GB para Selenium
- Reinicio automático con `restart: unless-stopped`

---

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Configuración del servidor
HOST=0.0.0.0
PORT=8000
```

**Valores por defecto:**
- `HOST`: `0.0.0.0` (todas las interfaces)
- `PORT`: `8000`

### Configuración del Scraper

El scraper se ejecuta en modo headless por defecto. Para ver el navegador durante desarrollo, modifica `scraper.py`:

```python
# Línea ~30 en scraper.py
# Comentar esta línea para ver el navegador:
# options.add_argument('--headless=new')
```

---

## Uso

### 1. API REST (FastAPI)

#### Iniciar el servidor

**Desarrollo local:**
```bash
uvicorn api:app --reload
```

**Docker:**
```bash
docker compose up
```

**Producción (sin Docker):**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Ejemplos de Requests

**Consulta básica:**
```bash
curl http://localhost:8000/consultar/20267367146
```

**Consulta con trabajadores:**
```bash
curl "http://localhost:8000/consultar/20267367146?trabajadores=true"
```

**Consulta completa (todos los datos):**
```bash
curl "http://localhost:8000/consultar/20267367146?trabajadores=true&representantes=true&historico=true&deuda_coactiva=true&reactiva_peru=true&programa_covid19=true&establecimientos=true"
```

**Consulta en lote con threading:**
```bash
curl -X POST "http://localhost:8000/consultar-lote" \
  -H "Content-Type: application/json" \
  -d '{
    "rucs": ["20267367146", "20100070970", "20131312955"],
    "trabajadores": true,
    "representantes": true,
    "use_threading": true,
    "max_workers": 3
  }'
```

#### Respuesta Ejemplo

```json
{
  "ruc": "20267367146",
  "numero_ruc": "20267367146",
  "razon_social": "EMPRESA EJEMPLO SAC",
  "tipo_contribuyente": "SOCIEDAD ANONIMA CERRADA",
  "nombre_comercial": "EJEMPLO STORE",
  "estado": "ACTIVO",
  "condicion": "HABIDO",
  "direccion_fiscal": "AV. EJEMPLO 123 - LIMA - LIMA - SAN ISIDRO",
  "fecha_inscripcion": "01/01/2010",
  "fecha_inicio_actividades": "01/02/2010",
  "fecha_consulta": "2025-12-12 15:30:45",
  "actividades_economicas": [
    {
      "principal": true,
      "codigo": "47111",
      "descripcion": "VENTA AL POR MENOR EN COMERCIOS NO ESPECIALIZADOS"
    }
  ],
  "comprobantes_pago": ["FACTURA", "BOLETA DE VENTA"],
  "sistema_emision_comprobante": "MANUAL/COMPUTARIZADO",
  "sistema_contabilidad": "COMPUTARIZADO",
  "cantidad_trabajadores": [
    {
      "periodo": "2024/11",
      "trabajadores": "15",
      "pensionistas": "0",
      "prestadores_servicio": "3"
    }
  ],
  "representantes_legales": [
    {
      "cargo": "GERENTE GENERAL",
      "nombre": "JUAN PEREZ LOPEZ",
      "desde": "01/01/2010"
    }
  ]
}
```

---

### 2. Línea de Comandos (CLI)

#### Consulta Simple

```bash
python cli.py 20267367146
```

#### Consulta con Trabajadores

```bash
python cli.py 20267367146 --trabajadores
```

#### Consulta con Representantes Legales

```bash
python cli.py 20267367146 --representantes
```

#### Consulta con Información Histórica

```bash
python cli.py 20267367146 --historico
```

#### Consulta Completa (Todos los Datos)

```bash
python cli.py 20267367146 \
  --trabajadores \
  --representantes \
  --historico \
  --deuda-coactiva \
  --reactiva-peru \
  --programa-covid19 \
  --establecimientos-anexos
```

#### Consulta Múltiple (Varios RUCs)

**Con lista manual:**
```bash
python cli.py --rucs 20267367146,20100070970,20131312955 --trabajadores
```

**Desde archivo:**
```bash
# Crear archivo con RUCs (uno por línea)
echo "20267367146" > rucs.txt
echo "20100070970" >> rucs.txt
echo "20131312955" >> rucs.txt

# Ejecutar consulta
python cli.py --archivo rucs.txt --trabajadores --representantes
```

#### Guardar Resultados en Archivo

```bash
python cli.py 20267367146 --trabajadores -o resultado.json
```

#### Opciones Disponibles del CLI

```
Uso: python cli.py [RUC] [OPCIONES]

RUC (uno de los siguientes):
  ruc                          # RUC individual (11 dígitos)
  --rucs LISTA                 # Múltiples RUCs separados por comas
  --archivo ARCHIVO            # Archivo con RUCs (uno por línea)

Opciones de datos:
  --trabajadores               # Incluir cantidad de trabajadores
  --representantes             # Incluir representantes legales
  --historico                  # Incluir información histórica
  --deuda-coactiva            # Incluir deuda coactiva
  --reactiva-peru             # Incluir información de Reactiva Perú
  --programa-covid19          # Incluir Programa de Garantías COVID-19
  --establecimientos-anexos   # Incluir establecimientos anexos

Salida:
  -o, --output ARCHIVO         # Guardar resultados en archivo JSON
```

---

## 🌐 Endpoints de la API

### `GET /`
**Descripción:** Información general de la API

**Respuesta:**
```json
{
  "nombre": "API Consulta RUC SUNAT",
  "version": "1.0.0",
  "endpoints": [...]
}
```

---

### `GET /health`
**Descripción:** Verificar estado de la API

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-12T15:30:45"
}
```

---

### `GET /consultar/{ruc}`
**Descripción:** Consulta información de un RUC individual

**Parámetros de ruta:**
- `ruc` (string, requerido): Número de RUC de 11 dígitos

**Parámetros de query (todos opcionales):**
- `trabajadores` (boolean, default: false): Incluir datos de trabajadores
- `representantes` (boolean, default: false): Incluir representantes legales
- `historico` (boolean, default: false): Incluir información histórica
- `deuda_coactiva` (boolean, default: false): Incluir deuda coactiva
- `reactiva_peru` (boolean, default: false): Incluir Reactiva Perú
- `programa_covid19` (boolean, default: false): Incluir Programa COVID-19
- `establecimientos` (boolean, default: false): Incluir establecimientos anexos

**Respuestas:**
- `200`: Datos del RUC encontrados
- `400`: RUC inválido (formato incorrecto)
- `404`: RUC no encontrado
- `500`: Error interno del servidor

**Ejemplo:**
```bash
curl "http://localhost:8000/consultar/20267367146?trabajadores=true&representantes=true"
```

---

### `POST /consultar-lote`
**Descripción:** Consulta múltiples RUCs en lote con soporte de threading

**Body (JSON):**
```json
{
  "rucs": ["20267367146", "20100070970"],
  "trabajadores": true,
  "representantes": true,
  "historico": false,
  "deuda_coactiva": false,
  "reactiva_peru": false,
  "programa_covid19": false,
  "establecimientos": false,
  "use_threading": true,
  "max_workers": 3
}
```

**Parámetros:**
- `rucs` (array[string], requerido): Lista de RUCs a consultar
- `trabajadores` (boolean, default: false): Incluir trabajadores
- `representantes` (boolean, default: false): Incluir representantes
- `historico` (boolean, default: false): Incluir histórico
- `deuda_coactiva` (boolean, default: false): Incluir deuda coactiva
- `reactiva_peru` (boolean, default: false): Incluir Reactiva Perú
- `programa_covid19` (boolean, default: false): Incluir COVID-19
- `establecimientos` (boolean, default: false): Incluir establecimientos
- `use_threading` (boolean, default: true): Usar procesamiento paralelo
- `max_workers` (integer, default: 3): Número máximo de hilos simultáneos

**Respuesta:**
```json
{
  "total": 2,
  "exitosos": 2,
  "fallidos": 0,
  "tiempo_procesamiento": "12.34s",
  "resultados": [
    {
      "success": true,
      "ruc": "20267367146",
      "numero_ruc": "20267367146",
      "razon_social": "EMPRESA 1 SAC",
      ...
    },
    {
      "success": true,
      "ruc": "20100070970",
      "numero_ruc": "20100070970",
      "razon_social": "EMPRESA 2 SAC",
      ...
    }
  ]
}
```

**Ventajas del threading:**
- Hasta 3x más rápido para lotes grandes
- Procesamiento paralelo configurable
- Reporte de tiempo de procesamiento
- Manejo individual de errores por RUC

---

## Datos que Extrae

### Información Básica (Siempre)
- Número de RUC
- Razón Social
- Tipo de Contribuyente
- Nombre Comercial
- Estado (ACTIVO/BAJA/SUSPENSIÓN)
- Condición (HABIDO/NO HABIDO)
- Dirección Fiscal completa
- Fecha de Inscripción
- Fecha de Inicio de Actividades
- Fecha de Consulta (timestamp)

### Información Tributaria (Siempre)
- Actividades Económicas (CIIU) con indicador principal
- Comprobantes de Pago autorizados
- Sistema de Emisión de Comprobantes
- Sistema de Contabilidad
- Afiliación al PLE (Programa de Libros Electrónicos)
- Padrones registrados

### Información Extendida (Opcional)

#### Cantidad de Trabajadores (`--trabajadores`)
Array de períodos con:
- Período (YYYY/MM)
- Número de trabajadores
- Número de pensionistas
- Número de prestadores de servicio

#### Representantes Legales (`--representantes`)
Array con:
- Cargo
- Nombre completo
- Fecha de designación

#### Información Histórica (`--historico`)
- Nombres/Razones Sociales anteriores con fechas
- Direcciones fiscales anteriores con fechas
- Condiciones históricas con fechas

#### Deuda Coactiva (`--deuda-coactiva`)
Array de deudas remitidas a centrales de riesgo con:
- Número de expediente
- Entidad
- Monto total adeudado
- Estado

#### Reactiva Perú (`--reactiva-peru`)
- Estado de beneficiario
- Información del programa

#### Programa COVID-19 (`--programa-covid19`)
- Programa de Garantías COVID-19
- Estado de participación

#### Establecimientos Anexos (`--establecimientos-anexos`)
Array de sucursales/establecimientos con:
- Código de establecimiento
- Dirección completa
- Distrito
- Departamento
- Estado

---

## Tecnologías Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)** (v0.115.6): Framework web moderno y de alto rendimiento
- **[Selenium](https://www.selenium.dev/)** (v4.27.1): Automatización de navegadores web
- **[Pydantic](https://docs.pydantic.dev/)** (v2.10.4): Validación de datos y configuración
- **[Uvicorn](https://www.uvicorn.org/)** (v0.34.0): Servidor ASGI de alto rendimiento
- **[WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)** (v4.0.2): Gestión automática de drivers
- **[Docker](https://www.docker.com/)**: Containerización para despliegue consistente
- **Python** 3.11+: Lenguaje de programación

---

## � Troubleshooting

### Error: "chrome not reachable" o "session deleted"

**Causa:** Chrome no está instalado o no es compatible con el driver.

**Solución:**
```bash
# Verificar versión de Chrome
google-chrome --version

# Reinstalar webdriver-manager
pip install --upgrade webdriver-manager
```

### Error: "Unable to locate element"

**Causa:** SUNAT cambió la estructura HTML de su página.

**Solución:** Actualiza los selectores en `scraper.py` o reporta un issue.


**Solución:**
```bash
# Cambiar puerto en .env
PORT=8001### Error: Puerto 8000 ya en uso


# O especificar al iniciar
uvicorn api:app --port 8001
```

### Docker: Error al construir la imagen

**Solución:**
```bash
# Limpiar caché de Docker
docker builder prune -a

# Reconstruir desde cero
docker compose build --no-cache
```

### Performance: Consultas en lote muy lentas

**Solución:** Habilita threading en el endpoint de lote:
```json
{
  "rucs": [...],
  "use_threading": true,
  "max_workers": 5
}
```

> **Nota:** No uses más de 5 workers para evitar sobrecargar SUNAT.

### Error: Timeout esperando elemento

**Solución:** Aumenta el timeout en `scraper.py`:
```python
wait = WebDriverWait(self.driver, 20)  # Aumentar a 20 segundos
```

---

### Modo de desarrollo

Para desarrollo activo con hot-reload:

```bash
uvicorn api:app --reload --log-level debug

docker compose up
```

---


## Licencia

Este proyecto está bajo la Licencia MIT.

---


