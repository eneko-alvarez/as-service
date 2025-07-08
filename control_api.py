from flask import Flask, request, jsonify
import subprocess
import os
import signal
import time
import requests
import psutil

app = Flask(__name__)

# Almacenar PIDs activos
active_streams = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "acestream-control"})

@app.route('/start_stream', methods=['POST'])
def start_stream():
    data = request.json
    stream_id = data.get('stream_id')
    
    if not stream_id:
        return jsonify({"error": "stream_id required"}), 400
    
    # Limpiar streams anteriores
    stop_all_streams()
    
    try:
        logger.debug(f"Iniciando stream con ID: {stream_id}")
        cmd = ["acestreamengine", "--client-console", f"--stream-id={stream_id}", "--port=6878"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Esperar un poco para ver si se inicia
        time.sleep(5)
        
        # Capturar salida para depuración
        stdout, stderr = process.communicate(timeout=10)
        logger.debug(f"stdout: {stdout}")
        logger.error(f"stderr: {stderr}")
        
        # Verificar si el proceso sigue vivo
        if process.poll() is None:
            active_streams[stream_id] = process.pid
            # Usar el dominio público de Railway o una URL personalizada
            domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'as-service-production.up.railway.app')
            stream_url = f"https://{domain}/ace/getstream?id={stream_id}"
            
            logger.info(f"Stream iniciado: {stream_id}, URL: {stream_url}")
            return jsonify({
                "status": "started",
                "stream_id": stream_id,
                "stream_url": stream_url,
                "pid": process.pid,
                "method": "acestream-engine"
            })
        else:
            logger.error(f"acestream-engine falló: {stderr}")
            raise Exception(f"acestream-engine terminó inesperadamente: {stderr}")
                
    except Exception as e:
        logger.error(f"Error en método 1: {str(e)}")
        
        # Método 2: Intentar con el servicio web existente
        try:
            service_url = "http://localhost:8080/search.m3u"
            logger.debug(f"Probando servicio web: {service_url}")
            response = requests.get(service_url, timeout=5)
            if response.status_code == 200:
                logger.info("Servicio web encontrado")
                return jsonify({
                    "status": "started",
                    "stream_id": stream_id,
                    "stream_url": f"http://localhost:8080/search.m3u?id={stream_id}",
                    "method": "web-service"
                })
            else:
                raise Exception(f"Web service respondió con código {response.status_code}")
        except Exception as e2:
            logger.error(f"Error en método 2: {str(e2)}")
            
            # Método 3: Usar URL externa como fallback
            domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'as-service-production.up.railway.app')
            external_url = f"https://{domain}/ace/getstream?id={stream_id}"
            logger.warning(f"Usando fallback externo: {external_url}")
            return jsonify({
                "status": "started",
                "stream_id": stream_id,
                "stream_url": external_url,
                "method": "external",
                "message": "Stream preparado - puede que necesite unos segundos para iniciar"
            })
        
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        return jsonify({"error": f"Error starting stream: {str(e)}"}), 500

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    data = request.json
    stream_id = data.get('stream_id')
    
    if stream_id and stream_id in active_streams:
        try:
            pid = active_streams[stream_id]
            os.kill(pid, signal.SIGTERM)
            del active_streams[stream_id]
            return jsonify({"status": "stopped", "stream_id": stream_id})
        except Exception as e:
            return jsonify({"error": f"Error stopping stream: {str(e)}"}), 500
    
    # Fallback: matar todos los procesos acestream
    stop_all_streams()
    return jsonify({"status": "all_stopped"})

def stop_all_streams():
    try:
        # Matar procesos acestream
        for proc in psutil.process_iter(['pid', 'name']):
            if 'acestream' in proc.info['name'].lower():
                proc.terminate()
        
        # Limpiar diccionario
        active_streams.clear()
    except:
        pass

@app.route('/status', methods=['GET'])
def get_status():
    # Verificar que acestream está disponible
    acestream_available = False
    try:
        result = subprocess.run(['which', 'acestreamengine'], capture_output=True, text=True)
        acestream_available = result.returncode == 0
    except:
        pass
    
    return jsonify({
        "active_streams": len(active_streams),
        "streams": list(active_streams.keys()),
        "acestream_available": acestream_available,
        "system": "runninggggg"
    })

# Endpoint para probar comunicación con acestream
@app.route('/test_acestream', methods=['GET'])
def test_acestream():
    try:
        # Test 1: Verificar si acestream está instalado
        result = subprocess.run(['which', 'acestreamengine'], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({
                "status": "ok",
                "acestream_path": result.stdout.strip(),
                "message": "AceStream engine encontrado"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "AceStream engine no encontrado",
                "suggestion": "Verificar instalación"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error verificando AceStream: {str(e)}"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)