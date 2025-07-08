from flask import Flask, request, jsonify
import subprocess
import os
import signal
import time
import requests
import psutil
import logging
import threading
import json

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Almacenar PIDs activos
active_streams = {}

def find_acestream_binary():
    """Buscar y devolver el path del binario principal de AceStream"""
    try:
        # Buscar binarios
        result = subprocess.run(['find', '/opt/acestream', '-name', 'acestreamengine', '-type', 'f'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            paths = result.stdout.strip().split('\n')
            logger.debug(f"Binarios encontrados: {paths}")
            
            # Filtrar para evitar el de /lib/ y tomar el principal
            main_binary = None
            for path in paths:
                if path and '/lib/' not in path:
                    main_binary = path
                    break
            
            # Si no encontramos uno principal, usar el primero
            if not main_binary and paths:
                main_binary = paths[0]
            
            logger.debug(f"Binario seleccionado: {main_binary}")
            return main_binary
        
        # Fallback: intentar con el enlace simbólico
        if os.path.exists('/usr/bin/acestreamengine'):
            return '/usr/bin/acestreamengine'
            
    except Exception as e:
        logger.error(f"Error buscando binario: {str(e)}")
    
    return None

def is_acestream_working():
    """Verificar si AceStream está funcionando correctamente"""
    try:
        acestream_binary = find_acestream_binary()
        if not acestream_binary or not os.path.exists(acestream_binary):
            return False
        
        # En lugar de --version, vamos a probar con --help que es más estándar
        # o simplemente verificar que el binario existe y es ejecutable
        import stat
        file_stat = os.stat(acestream_binary)
        is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
        
        # Verificar que las dependencias están resueltas
        ldd_result = subprocess.run(['ldd', acestream_binary], capture_output=True, text=True, timeout=10)
        dependencies_ok = "not found" not in ldd_result.stdout
        
        return is_executable and dependencies_ok
        
    except Exception as e:
        logger.error(f"Error verificando AceStream: {str(e)}")
        return False

def start_acestream_daemon():
    """Iniciar el daemon de AceStream en background"""
    try:
        acestream_binary = find_acestream_binary()
        if not acestream_binary:
            raise Exception("AceStream binary not found")
        
        # Comando para iniciar el daemon
        cmd = [
            acestream_binary,
            "--client-console",
            "--port=6878",
            "--bind-all",
            "--log-file=/tmp/acestream.log",
            "--log-level=debug"
        ]
        
        logger.info(f"Iniciando daemon AceStream: {' '.join(cmd)}")
        
        # Iniciar el proceso
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        
        # Dar tiempo al daemon para iniciar
        time.sleep(10)
        
        return process
        
    except Exception as e:
        logger.error(f"Error iniciando daemon AceStream: {str(e)}")
        return None

def check_acestream_port():
    """Verificar si el puerto 6878 está disponible"""
    try:
        result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
        return ":6878 " in result.stdout
    except:
        return False

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
        
        # Verificar que AceStream está funcionando
        if not is_acestream_working():
            raise Exception("AceStream no está disponible")
        
        # Método 1: Intentar con el daemon
        acestream_binary = find_acestream_binary()
        
        # Comando simplificado para stream específico
        cmd = [
            acestream_binary,
            "--client-console",
            "--startup-connect",
            f"--stream-id={stream_id}",
            "--port=6878",
            "--bind-all"
        ]
        
        logger.info(f"Ejecutando comando: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        
        # Esperar un poco más para que el stream se establezca
        time.sleep(20)
        
        # Verificar si el proceso sigue ejecutándose
        if process.poll() is None:
            active_streams[stream_id] = process.pid
            domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8080')
            stream_url = f"http://127.0.0.1:6878/ace/getstream?id={stream_id}"
            
            logger.info(f"Stream iniciado: {stream_id}, URL: {stream_url}")
            return jsonify({
                "status": "started",
                "stream_id": stream_id,
                "stream_url": stream_url,
                "local_url": f"http://127.0.0.1:6878/ace/getstream?id={stream_id}",
                "pid": process.pid,
                "method": "acestream-engine"
            })
        else:
            # Obtener logs del proceso
            stdout, stderr = process.communicate()
            logger.error(f"AceStream terminó inesperadamente")
            logger.error(f"stdout: {stdout}")
            logger.error(f"stderr: {stderr}")
            
            # Intentar método alternativo
            return start_stream_alternative(stream_id)
                
    except Exception as e:
        logger.error(f"Error en método principal: {str(e)}")
        return start_stream_alternative(stream_id)

def start_stream_alternative(stream_id):
    """Método alternativo para iniciar stream"""
    try:
        logger.info(f"Intentando método alternativo para stream: {stream_id}")
        
        # Verificar si hay un servicio web disponible
        try:
            service_url = "http://localhost:8080/search.m3u"
            response = requests.get(service_url, timeout=5)
            if response.status_code == 200:
                logger.info("Servicio web encontrado")
                return jsonify({
                    "status": "started",
                    "stream_id": stream_id,
                    "stream_url": f"http://localhost:8080/search.m3u?id={stream_id}",
                    "method": "web-service"
                })
        except:
            pass
        
        # Fallback: URL externa
        domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8080')
        external_url = f"http://127.0.0.1:6878/ace/getstream?id={stream_id}"
        
        logger.warning(f"Usando fallback: {external_url}")
        return jsonify({
            "status": "started",
            "stream_id": stream_id,
            "stream_url": external_url,
            "method": "fallback",
            "message": "Stream configurado - puede necesitar tiempo adicional para inicializar"
        })
        
    except Exception as e:
        logger.error(f"Error en método alternativo: {str(e)}")
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
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    logger.debug(f"Terminado proceso: {proc.info['name']} (PID: {proc.pid})")
                except:
                    pass
        active_streams.clear()
    except Exception as e:
        logger.error(f"Error deteniendo streams: {str(e)}")

@app.route('/status', methods=['GET'])
def get_status():
    acestream_available = is_acestream_working()
    port_available = check_acestream_port()
    
    return jsonify({
        "active_streams": len(active_streams),
        "streams": list(active_streams.keys()),
        "acestream_available": acestream_available,
        "port_6878_active": port_available,
        "system": "running"
    })

@app.route('/test_acestream', methods=['GET'])
def test_acestream():
    try:
        acestream_binary = find_acestream_binary()
        if acestream_binary:
            logger.debug(f"Probando binario: {acestream_binary}")
            
            # Verificar permisos del archivo
            import stat
            file_stat = os.stat(acestream_binary)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
            
            # Verificar dependencias
            ldd_result = subprocess.run(['ldd', acestream_binary], capture_output=True, text=True, timeout=10)
            dependencies_ok = "not found" not in ldd_result.stdout
            
            # En lugar de --version, intentar con --help
            try:
                result = subprocess.run([acestream_binary, '--help'], capture_output=True, text=True, timeout=5)
                help_works = True
                help_output = result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
            except:
                help_works = False
                help_output = "No disponible"
            
            if is_executable and dependencies_ok:
                return jsonify({
                    "status": "ok",
                    "message": "AceStream engine disponible",
                    "path": acestream_binary,
                    "is_executable": is_executable,
                    "dependencies_ok": dependencies_ok,
                    "help_works": help_works,
                    "help_output": help_output
                })
            else:
                return jsonify({
                    "status": "warning",
                    "message": "AceStream engine encontrado pero con problemas",
                    "path": acestream_binary,
                    "is_executable": is_executable,
                    "dependencies_ok": dependencies_ok,
                    "missing_deps": [line for line in ldd_result.stdout.split('\n') if 'not found' in line]
                })
        else:
            return jsonify({
                "status": "error",
                "message": "AceStream binary no encontrado",
                "suggestion": "Verificar instalación en /opt/acestream"
            })
            
    except Exception as e:
        logger.error(f"Error verificando AceStream: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error verificando AceStream: {str(e)}"
        })

@app.route('/debug_acestream', methods=['GET'])
def debug_acestream():
    """Endpoint para diagnosticar problemas con AceStream"""
    try:
        acestream_binary = find_acestream_binary()
        debug_info = {
            "binary_path": acestream_binary,
            "binary_exists": os.path.exists(acestream_binary) if acestream_binary else False
        }
        
        if acestream_binary and os.path.exists(acestream_binary):
            import stat
            file_stat = os.stat(acestream_binary)
            debug_info.update({
                "file_size": file_stat.st_size,
                "is_executable": bool(file_stat.st_mode & stat.S_IEXEC),
                "permissions": oct(file_stat.st_mode)[-3:]
            })
            
            # Verificar dependencias
            try:
                ldd_result = subprocess.run(['ldd', acestream_binary], capture_output=True, text=True, timeout=10)
                debug_info["dependencies_resolved"] = "not found" not in ldd_result.stdout
                debug_info["ldd_output"] = ldd_result.stdout
            except Exception as e:
                debug_info["ldd_error"] = str(e)
            
            # Verificar tipo de archivo
            try:
                file_result = subprocess.run(['file', acestream_binary], capture_output=True, text=True, timeout=5)
                debug_info["file_type"] = file_result.stdout
            except Exception as e:
                debug_info["file_type_error"] = str(e)
            
            # Intentar ejecutar con diferentes argumentos
            test_commands = [
                ['--help'],
                ['--version'],
                ['-h'],
                []
            ]
            
            debug_info["execution_tests"] = {}
            for cmd_args in test_commands:
                try:
                    result = subprocess.run([acestream_binary] + cmd_args, 
                                          capture_output=True, text=True, timeout=5)
                    debug_info["execution_tests"][str(cmd_args)] = {
                        "return_code": result.returncode,
                        "stdout": result.stdout[:500],
                        "stderr": result.stderr[:500]
                    }
                except subprocess.TimeoutExpired:
                    debug_info["execution_tests"][str(cmd_args)] = {"error": "timeout"}
                except Exception as e:
                    debug_info["execution_tests"][str(cmd_args)] = {"error": str(e)}
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": f"Error en debug: {str(e)}"
        })

@app.route('/start_daemon', methods=['POST'])
def start_daemon():
    """Iniciar el daemon de AceStream manualmente"""
    try:
        daemon_process = start_acestream_daemon()
        if daemon_process:
            return jsonify({
                "status": "started",
                "message": "Daemon AceStream iniciado",
                "pid": daemon_process.pid
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No se pudo iniciar el daemon"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error iniciando daemon: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)