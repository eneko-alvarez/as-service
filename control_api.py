from flask import Flask, request, jsonify
import subprocess
import os
import signal
import psutil
import requests
import time

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
    
    # Matar streams anteriores
    stop_all_streams()
    
    try:
        # Iniciar AceStream engine
        process = subprocess.Popen([
            'acestreamengine',
            '--client-console',
            f'--stream-id={stream_id}',
            '--port=6878'
        ])
        
        active_streams[stream_id] = process.pid
        
        # Esperar a que se inicie
        time.sleep(5)
        
        stream_url = f"http://127.0.0.1:6878/ace/getstream?id={stream_id}"
        
        return jsonify({
            "status": "started",
            "stream_id": stream_id,
            "stream_url": stream_url,
            "pid": process.pid
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        except:
            pass
    
    # Fallback: matar todos los procesos acestream
    stop_all_streams()
    return jsonify({"status": "all_stopped"})

@app.route('/stop_all', methods=['POST'])
def stop_all():
    stop_all_streams()
    return jsonify({"status": "all_stopped"})

def stop_all_streams():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'acestream' in proc.info['name'].lower():
                proc.terminate()
    except:
        pass
    active_streams.clear()

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "active_streams": len(active_streams),
        "streams": list(active_streams.keys())
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
