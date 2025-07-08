# Usar imagen base Ubuntu 22.04
FROM ubuntu:22.04

# Establecer variables de entorno para evitar interacciones interactivas
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar e instalar dependencias básicas
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    python3 \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configurar el repositorio de AceStream
RUN wget -q -O - http://acestream.org/keys/acestream.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/acestream.gpg && \
    echo "deb http://repo.acestream.org/ubuntu/ bionic main" > /etc/apt/sources.list.d/acestream.list

# Actualizar e instalar acestream-engine
RUN apt-get update && \
    apt-get install -y --no-install-recommends acestream-engine || { echo "Error instalando acestream-engine"; exit 1; } && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Instalar dependencias Python
RUN pip3 install --no-cache-dir flask psutil requests

# Crear directorio de trabajo
WORKDIR /app

# Copiar la API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar la API
CMD ["python3", "control_api.py"]