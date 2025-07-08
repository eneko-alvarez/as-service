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
        # Intentar diferentes formas de ejecutar acestream
        possible_commands = [
            ['acestreamengine', '--client-console', f'--stream-id={stream_id}'],
            ['python3', '-m', 'acestream.core', '--client-console', f'--stream-id={stream_id}'],
            ['python', '-m', 'acestream.core', '--client-console', f'--stream-id={stream_id}']
        ]
        
        process = None
        for cmd in possible_commands:
            try:
                process = subprocess.Popen(cmd)
                break
            except FileNotFoundError:
                continue
        
        if process is None:
            return jsonify({"error": "acestream command not found"}), 500
        
        active_streams[stream_id] = process.pid
        
        # Esperar a que se inicie
        time.sleep(3)
        
        # Determinar la URL externa
        domain = os.environ.get('RAILWAY_STATIC_URL', 'localhost')
        if 'railway.app' in domain:
            stream_url = f"https://{domain}/ace/getstream?id={stream_id}"
        else:
            stream_url = f"http://localhost:6878/ace/getstream?id={stream_id}"
        
        return jsonify({
            "status": "started",
            "stream_id": stream_id,
            "stream_url": stream_url,
            "pid": process.pid
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
        except:
            pass
    
    # Fallback: matar todos los procesos acestream
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
        "streams": list(active_streams.keys()),
        "available_commands": check_available_commands()
    })

def check_available_commands():
    commands = ['acestreamengine', 'python3', 'python']
    available = []
    for cmd in commands:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
            available.append(cmd)
        except:
            pass
    return available

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)