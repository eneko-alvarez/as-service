# Usar imagen base con acestream-engine preinstalado
FROM magnetikonline/docker-acestream-server:latest

# Instalar dependencias Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip && \
    pip3 install --no-cache-dir flask psutil requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar la API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar la API
CMD ["python3", "control_api.py"]