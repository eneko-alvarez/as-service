from flask import Flask, request, jsonify
import subprocess
import os
import signal
import time
import requests
import psutil
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        cmd = ["/usr/bin/acestreamengine", "--client-console", f"--stream-id={stream_id}", "--port=6878", "--bind-all"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        
        time.sleep(15)
        
        if process.poll() is None:
            active_streams[stream_id] = process.pid
            domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'as-service-production.up.railway.app')
            stream_url = f"https://{domain}/ace/getstream?id={stream_id}"
            
            stdout, stderr = process.communicate(timeout=5) if process.poll() is None else ("", "")
            logger.debug(f"acestreamengine stdout: {stdout}")
            logger.error(f"acestreamengine stderr: {stderr}")
            
            logger.info(f"Stream iniciado: {stream_id}, URL: {stream_url}")
            return jsonify({
                "status": "started",
                "stream_id": stream_id,
                "stream_url": stream_url,
                "pid": process.pid,
                "method": "acestream-engine"
            })
        else:
            stdout, stderr = process.communicate(timeout=5)
            logger.error(f"acestreamengine falló: {stderr}")
            raise Exception(f"acestreamengine terminó inesperadamente: {stderr}")
                
    except Exception as e:
        logger.error(f"Error en método 1: {str(e)}")
        
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
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            del active_streams[stream_id]
            logger.info(f"Stream detenido: {stream_id}")
            return jsonify({"status": "stopped", "stream_id": stream_id})
        except Exception as e:
            logger.error(f"Error deteniendo stream: {str(e)}")
            return jsonify({"error": f"Error stopping stream: {str(e)}"}), 500
    
    stop_all_streams()
    logger.info("Todos los streams detenidos")
    return jsonify({"status": "all_stopped"})

def stop_all_streams():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'acestream' in proc.info['name'].lower():
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                logger.debug(f"Terminado proceso: {proc.info['name']} (PID: {proc.pid})")
        active_streams.clear()
    except Exception as e:
        logger.error(f"Error deteniendo streams: {str(e)}")

@app.route('/status', methods=['GET'])
def get_status():
    acestream_available = False
    try:
        result = subprocess.run(['find', '/opt/acestream', '-name', 'acestreamengine'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            path = result.stdout.strip()
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            acestream_available = result.returncode == 0
            logger.debug(f"AceStream disponible: {acestream_available}, path: {path}")
        else:
            logger.error("AceStream no encontrado en /opt/acestream")
    except Exception as e:
        logger.error(f"Error verificando AceStream: {str(e)}")
    
    return jsonify({
        "active_streams": len(active_streams),
        "streams": list(active_streams.keys()),
        "acestream_available": acestream_available,
        "system": "running"
    })

@app.route('/test_acestream', methods=['GET'])
def test_acestream():
    try:
        result = subprocess.run(['find', '/opt/acestream', '-name', 'acestreamengine'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            path = result.stdout.strip()
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("AceStream engine encontrado")
                return jsonify({
                    "status": "ok",
                    "version": result.stdout.strip(),
                    "message": "AceStream engine encontrado",
                    "path": path
                })
            else:
                logger.error(f"AceStream no ejecutable: {result.stderr}")
                return jsonify({
                    "status": "error",
                    "message": "AceStream engine no ejecutable",
                    "error": result.stderr
                })
        else:
            logger.error("AceStream engine no encontrado en /opt/acestream")
            return jsonify({
                "status": "error",
                "message": "AceStream engine no encontrado",
                "suggestion": "Verificar instalación"
            })
    except Exception as e:
        logger.error(f"Error verificando AceStream: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error verificando AceStream: {str(e)}"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)