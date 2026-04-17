# AFIP | ARCA WSN TO API

## Repositorio

```bash
git clone http://192.168.190.95/forgejo/noble/afip-services-api.git
git pull origin main   # actualizar
```

> Primera vez en una máquina nueva: ver [SETUP.md](http://192.168.190.95/forgejo/noble/workspace/raw/branch/main/SETUP.md) para configurar proxy y credenciales Git.

---


Esta API, desarrollada con FastAPI, integra los servicios de AFIP a través de sus web services (WSAA y WSN). El proyecto implementa autenticación JWT, control de rate limiting, logging personalizado y utiliza Docker Compose para facilitar su despliegue.

## Estructura del Proyecto

```bash

├── __init__.py
├── .env
├── .gitignore
├── Dockerfile
├── README.md
├── docker-compose.yml
├── main.py
├── requirements.txt
├── app
│   ├── __init__.py
│   ├── afip_ws
│   │   ├── __init__.py
│   │   ├── afip_config.py
│   │   ├── afip_gateway.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   └── ticket.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   └── wsaa_client.py
│   │   ├── utils
│   │       ├── __init__.py
│   │       ├── crypto_utils.py
│   │       ├── exceptions.py
│   │       ├── signing.py
│   │       └── tra_utils.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── inscription.py
│   │   ├── padron.py
│   │   └── utils.py
│   └── core
│       ├── __init__.py
│       ├── config.py
│       ├── dependencies.py
│       ├── exception_handlers.py
│       ├── limiter.py
│       ├── logger.py
│       ├── security.py
│       └── service.py
├── auth_afip
│   ├── certificado_afip_noble.crt
│   └── private_key
└── logs/

```

- **Dockerfile & docker-compose.yml:** Configuración para crear el contenedor y orquestar servicios.
- **main.py:** Punto de entrada de la aplicación.
- **requirements.txt:** Lista de dependencias de Python.
- **app/**: Contiene la lógica de la API.
  - **api/**: Rutas para autenticación, inscripción, padrón y utilidades.
  - **core/**: Configuración, dependencias, seguridad, logging y rate limiting.
  - **afip_ws/**: Módulos para la comunicación con los servicios de AFIP.
- **auth_afip/**: Credenciales de AFIP. **Requiere un certificado y una clave privada** para autenticarse correctamente con los servicios de AFIP.
- **logs/**: Carpeta para almacenar los logs generados por la aplicación.

## Dependencias

El proyecto utiliza las siguientes dependencias en Python:

- **fastapi**
- **uvicorn**
- **pydantic**
- **slowapi**
- **xmltodict**
- **zeep**
- **cryptography**
- **pydantic_settings**
- **logtail-python**
- **python-jose**
- **python-multipart**

## Configuración (.env)

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables (modifica los valores según tu entorno, revisar el archivo `.env.example`):

```env

# Configuración de la aplicación
DEBUG=False # True para activar el modo de depuración

# Logging
LOG_DIR_PATH=<ruta_log> # Ruta del directorio de logs
LOGTAIL_TOKEN=<tu_logtail_token> # Opcional

# Autenticación
AUTH_USERNAME=<usuario> # Usuario para autenticación JWT
AUTH_PASSWORD=<contraseña> # Contraseña para autenticación JWT
AUTH_SECRET_KEY=<clave_secreta> # Clave secreta para autenticación JWT
AUTH_ALGORITHM=HS256 # Algoritmo de encriptación para autenticación JWT
AUTH_EXPIRES_IN=30 # Tiempo de expiración del token JWT (en minutos)

# API
API_PREFIX="/api" # Prefijo para las rutas de la API
API_VERSION="v1" # Versión de la API

# Configuración de AFIP WSN
CERTIFICATE_PATH=<ruta_certificado_afip> # Ruta del certificado de AFIP
PRIVATE_KEY_PATH=<ruta_clave_privada> # Ruta de la clave privada de AFIP
PASSPHRASE=<opcional_si_corresponde> # Contraseña del certificado de AFIP (si aplica)

# SlowAPI Rate Limiting
RATE_LIMIT_TIME=60 # Tiempo de rate limiting (en segundos)
MAX_CALLS=1 # Cantidad máxima de llamadas permitidas

```

> **Importante:** Para utilizar los servicios de AFIP es obligatorio contar con las credenciales de AFIP, es decir, un certificado y una clave privada. Estos archivos se deben colocar en la carpeta que querramos, pero sus rutas deben configurarse en el archivo `.env` mediante las variables `CERTIFICATE_PATH` y `PRIVATE_KEY_PATH`. Si el certificado está protegido por una contraseña, se debe incluir en la variable `PASSPHRASE`. Tambien tener en cuenta si usamos docker, debemos montar el volumen o bien trabajar con el archivo `docker-compose.yml` en conjunto a `docker compose`(v2 preferentemente).

## Uso y Ejecución

### Ejecución Local

Se recomienda utilizar un entorno virtual para aislar las dependencias del proyecto.

1. **Crear y activar el entorno virtual:**

   - **En sistemas Unix/MacOS:**

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

   - **En Windows:**

     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

2. **Instalar las dependencias:**

   Una vez activado el entorno virtual, instala las dependencias mediante:

   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**

   Ejecuta la API con Uvicorn:

   ```bash
   uvicorn main:app
   ```
   - Cualquier duda revisar la documentación de FastAPI: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/). Se puede agregar el parámetro `--reload` para reiniciar automáticamente el servidor al detectar cambios en el código, entre otros parámetros.

### Ejecución con Docker Compose. Importante, se debe tener instalado Docker y Docker Compose en el sistema.

El proyecto incluye un `Dockerfile` y un archivo `docker-compose.yml` para facilitar el despliegue.

1. **Construir y levantar el contenedor:**

   ```bash
   docker compose up -d --build # Para construir y levantar el contenedor en segundo plano Docker Compose v2
   ```

2. **Acceder a la API:**

   La API estará disponible en el puerto configurado en el `docker-compose.yml` (por defecto, el puerto 8000, cambiar en Dockerfile).

## Endpoints Principales

- **Health Check:**  
  `GET /`  
  Devuelve información básica de la API (nombre, versión y descripción).

- **Autenticación (JWT):**  
  `POST /api/v1/token`  
  Genera un token de acceso JWT mediante las credenciales definidas en el `.env`.

- **Inscripción:**  
  - `POST /api/v1/inscription`  
    Realiza consultas al servicio de inscripción de AFIP.
  - `GET /api/v1/inscription/health`  
    Verifica el estado del servicio de inscripción.

- **Padrón:**  
  - `POST /api/v1/padron`  
    Realiza consultas al servicio de padrón de AFIP.
  - `GET /api/v1/padron/health`  
    Verifica el estado del servicio de padrón.

> **Nota:** Para acceder a los endpoints protegidos, es necesario incluir el token JWT en el header `Authorization` con el formato: `Bearer <token>`.

## Consideraciones Adicionales

- **Rate Limiting:**  
  Se limita la cantidad de llamadas definidas en el archivo `.env` (por defecto, 1 llamada cada 60 segundos).

- **Logging:**  
  Los logs se generan en la carpeta `logs` y están configurados para rotación y para integrarse con Logtail si se provee el token. En caso de usar docker, agregar el volumen en el archivo `docker-compose.yml`. Ver el archivo `docker-compose-example.yml` para más detalles.

- **Servicios de AFIP:**  
  La autenticación con AFIP se realiza mediante WSAA, y se gestionan dos servicios (Inscripción y Padrón) mediante la clase `WSN`.

- **Credenciales de AFIP:**  
  Es indispensable contar con las credenciales (certificado y clave privada) para poder realizar la autenticación y consumir los servicios de AFIP. Estos deben estar correctamente ubicados y configurados en el archivo `.env`.

## Contribución

Si deseas contribuir al proyecto, por favor, realiza un fork, implementa tus cambios y envía un pull request.

## Licencia

Este proyecto es de código abierto y se distribuye bajo la licencia MIT.