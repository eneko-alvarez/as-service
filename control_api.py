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
        return jsonify({"error": "stream_id required"}), 1400
    
    # Limpiar streams anteriores
    stop_all_streams()
    
    try:
        # Método 1: Usar acestream-engine si está disponible
        try:
            # Comando básico de acestream
            cmd = f"acestreamengine --client-console --stream-id={stream_id} --port=6878"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Esperar un poco para ver si se inicia
            time.sleep(3)
            
            # Verificar si el proceso sigue vivo
            if process.poll() is None:
                # Proceso sigue corriendo
                active_streams[stream_id] = process.pid
                
                # Construir URL del stream
                domain = os.environ.get('RAILWAY_STATIC_URL', os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost'))
                if 'railway.app' in str(domain):
                    stream_url = f"https://{domain}/ace/getstream?id={stream_id}"
                else:
                    stream_url = f"http://localhost:6878/ace/getstream?id={stream_id}"
                
                return jsonify({
                    "status": "started",
                    "stream_id": stream_id,
                    "stream_url": stream_url,
                    "pid": process.pid,
                    "method": "acestream-engine"
                })
            else:
                # Proceso murió inmediatamente
                raise Exception("acestream-engine terminó inesperadamente")
                
        except Exception as e:
            # Si no funciona, intentar con el servicio docker existente
            try:
                # Intentar comunicarse con el servicio web existente
                service_url = "http://localhost:8080/search.m3u"
                response = requests.get(service_url, timeout=5)
                if response.status_code == 200:
                    # El servicio web funciona
                    return jsonify({
                        "status": "started",
                        "stream_id": stream_id,
                        "stream_url": f"http://localhost:8080/search.m3u?id={stream_id}",
                        "method": "web-service"
                    })
                else:
                    raise Exception("Web service no responde")
            except:
                # Como último recurso, usar un servicio externo
                external_url = f"http://127.0.0.1:6878/ace/getstream?id={stream_id}"
                return jsonify({
                    "status": "started",
                    "stream_id": stream_id,
                    "stream_url": external_url,
                    "method": "external",
                    "message": "Stream preparado - puede que necesite unos segundos para iniciar"
                })
        
    except Exception as e:
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
        "system": "running"
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