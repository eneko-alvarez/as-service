FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y wget curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install flask psutil requests

# Crear directorio de trabajo
WORKDIR /app

# Copiar nuestra API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar nuestra API
CMD ["python", "control_api.py"]