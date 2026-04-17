FROM python:3.12-slim

# Instala tzdata para soporte de zonas horarias
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el contenido del proyecto
COPY . /app

# Crea entorno virtual
RUN python -m venv /app/.venv_docker
ENV VIRTUAL_ENV=/app/.venv_docker
ENV PATH="/app/.venv_docker/bin:$PATH"

# Actualiza pip e instala las dependencias
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expone el puerto 8000 en el contenedor
EXPOSE 8000

# Comando para arrancar la aplicación usando uvicorn en el puerto 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
