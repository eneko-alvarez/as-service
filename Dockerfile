FROM vstavrinov/acestream-engine

# Cambiar a usuario root temporalmente
USER root

# Crear directorio si no existe y actualizar
RUN mkdir -p /var/lib/apt/lists/partial && \
    apt-get update && \
    apt-get install -y python3-pip && \
    apt-get clean && \
    rm-rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip3 install flask psutil requests

# Copiar nuestra API
COPY control_api.py /app/
WORKDIR /app

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar nuestra API
CMD ["python3", "control_api.py"]