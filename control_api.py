from flask import Flask, request, jsonify
import subprocess
import os
import signal
import time
import json

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
    
    try:
        # Simular inicio de stream (para testing)
        # En producción aquí iría el comando real de acestream
        
        # Obtener dominio de Railway
        domain = os.environ.get('RAILWAY_STATIC_URL', 'localhost')
        if 'railway.app' in domain:
            stream_url = f"https://{domain}/stream/{stream_id}"
        else:
            stream_url = f"http://localhost:6878/ace/getstream?id={stream_id}"
        
        # Simular proceso activo
        active_streams[stream_id] = {
            'pid': 12345,
            'started_at': time.time(),
            'stream_url': stream_url
        }
        
        return jsonify({
            "status": "started",
            "stream_id": stream_id,
            "stream_url": stream_url,
            "message": "Stream preparado (versión de testing)"
        })
        
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    data = request.json
    stream_id = data.get('stream_id')
    
    if stream_id and stream_id in active_streams:
        del active_streams[stream_id]
        return jsonify({"status": "stopped", "stream_id": stream_id})
    
    return jsonify({"status": "not_found", "stream_id": stream_id})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "active_streams": len(active_streams),
        "streams": list(active_streams.keys()),
        "system": "running"
    })

@app.route('/stream/<stream_id>')
def stream_proxy(stream_id):
    # Aquí iría el proxy real del stream
    return f"Stream {stream_id} - En desarrollo"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)