FROM python:3.9-slim

# Cambiar a usuario root
USER root

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y wget curl gnupg2 software-properties-common && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar AceStream
RUN wget -qO- http://acestream.org/keys/acestream.asc | apt-key add - && \
    echo "deb http://repo.acestream.org/ubuntu/ bionic main" > /etc/apt/sources.list.d/acestream.list && \
    apt-get update && \
    apt-get install -y acestream-engine && \
    apt-get clean && \
    rm -rf /var/lib/apt/lis/*

# Instalar dependencias Python
RUN pip install flask psutil requests

# Copiar nuestra API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar nuestra API
CMD ["python", "control_api.py"]