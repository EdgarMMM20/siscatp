# Versión mejorada del archivo routes/operador.py con caché de IP para evitar múltiples consultas a la BD

import threading
import time
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
from db.db import *

BP_operador = Blueprint('BP_operador', __name__)

ESP32_TOKEN = "MiTokenSegur0!"
ESP32_MAC = "AC:15:18:D7:9A:AC"
DURACION_ACTIVACION = 5

# Cache local para IPs por MAC
_ip_cache = {}

# === Función para obtener IP desde base de datos por MAC ===
def obtener_ip_por_mac(mac):
    if mac in _ip_cache:
        return _ip_cache[mac]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ip FROM dispositivos WHERE mac = %s AND activo = 1", (mac,))
    result = cursor.fetchone()
    if result:
        _ip_cache[mac] = result['ip']
        return result['ip']
    return None

# === Consulta de zona de almacén por caja ===
@BP_operador.route('/consulta_caja', methods=['POST'])
def consulta_caja():
    data = request.get_json()
    cvcaja = data.get('cvcaja')
    idsucursal = session.get('idsucursal')

    if not cvcaja or not idsucursal:
        return jsonify({'error': 'Faltan datos requeridos'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.idzonalma
        FROM cajas c
        JOIN producto p ON c.cvpro = p.cvpro AND c.rfccomp = p.rfccomp
        JOIN tipopro t ON p.idtipo = t.idtipop
        JOIN zonalmacen z ON t.idzonalma = z.idzonalma
        WHERE c.cvcaja = %s AND z.idsucursal = %s
    """, (cvcaja, idsucursal))

    result = cursor.fetchone()

    if result:
        idzona = result['idzonalma']
        manejar_clasificacion_por_zona(idzona)
        return jsonify({'idzona': idzona})
    else:
        time.sleep(2)
        activar_servo('servo2')  # rechazo
        return jsonify({'error': 'Caja no encontrada'}), 404

# === Clasificación por zonas basada en ID de zona ===
def manejar_clasificacion_por_zona(idzona):
    time.sleep(2)

    if idzona in [1, 2, 3, 7]:  # Productos comestibles comunes
        print(f"Zona {idzona} → Canal A (servo1)")
        activar_servo('servo1')

    elif idzona in [4, 6]:  # Limpieza, no comestibles
        print(f"Zona {idzona} → Canal B (servo3)")
        activar_servo('servo3')

    elif idzona == 5:  # Productos sensibles (alimentación especial)
        print(f"Zona {idzona} → Canal C (sensor sin servo)")
        desactivar_sensor()
        time.sleep(0.5)
        activar_sensor()

    else:
        print(f"Zona {idzona} no reconocida. Activación omitida.")

# === Estado del sensor ===
def obtener_estado_sensor(mac=ESP32_MAC):
    ip = obtener_ip_por_mac(mac)
    if not ip:
        print("IP no encontrada para MAC:", mac)
        return False
    try:
        response = requests.get(f"http://{ip}/estado_sensor?token={ESP32_TOKEN}", timeout=5)
        if response.status_code == 200:
            return response.json().get("sensorActivo") == "true"
    except Exception as e:
        print("Error al obtener estado del sensor:", e)
    return False

# === Verificación automática ===
def verificar_sensor_duracion_automatico(duracion, mac=ESP32_MAC):
    tiempo_activo = 0
    estado_anterior = None
    while True:
        activo = obtener_estado_sensor(mac)
        if activo:
            tiempo_activo += 1
            if estado_anterior != True:
                print("Sensor activo, contando...")
            if tiempo_activo >= duracion:
                activar_servo('servo2', mac)
                tiempo_activo = 0
            estado_anterior = True
        else:
            if estado_anterior != False:
                print("Sensor inactivo.")
            tiempo_activo = 0
            estado_anterior = False
        time.sleep(1)

def iniciar_verificacion():
    thread = threading.Thread(target=verificar_sensor_duracion_automatico, args=(DURACION_ACTIVACION,))
    thread.daemon = True
    thread.start()

# === Comandos al ESP32 ===
def activar_servo(servo, mac=ESP32_MAC):
    ip = obtener_ip_por_mac(mac)
    if not ip:
        print(f"No se encontró IP para MAC {mac}")
        return
    try:
        url = f"http://{ip}/{servo}?token={ESP32_TOKEN}"
        print(f"Activando {servo} en {ip}")
        requests.get(url)
        desactivar_sensor(mac)
        time.sleep(0.5)
        activar_sensor(mac)
        time.sleep(3)
        requests.get(url)
    except Exception as e:
        print(f"Error al activar servo {servo}:", e)

def desactivar_sensor(mac=ESP32_MAC):
    ip = obtener_ip_por_mac(mac)
    if not ip:
        return
    try:
        requests.get(f"http://{ip}/desactivar_sensor?token={ESP32_TOKEN}")
    except:
        print("Error al desactivar sensor")

def activar_sensor(mac=ESP32_MAC):
    ip = obtener_ip_por_mac(mac)
    if not ip:
        return
    try:
        requests.get(f"http://{ip}/activar_sensor?token={ESP32_TOKEN}")
    except:
        print("Error al activar sensor")

# === Detención de caja por sensor ===
@BP_operador.route('/detectar_paquete', methods=['POST'])
def detectar_paquete():
    codigo = request.json.get('codigoBarra')
    if not codigo:
        return jsonify({'error': 'No se detectó un código de barras'}), 400

    ip = obtener_ip_por_mac(ESP32_MAC)
    if ip:
        print("Caja detectada:", codigo)
        requests.get(f"http://{ip}/desactivar_sensor?token={ESP32_TOKEN}")
        time.sleep(0.5)
        requests.get(f"http://{ip}/activar_sensor?token={ESP32_TOKEN}")
        return jsonify({'status': 'Procesado'})
    else:
        return jsonify({'error': 'Dispositivo no encontrado'}), 404

# === Consulta de mensajes serial del ESP32 ===
@BP_operador.route('/mensajes', methods=['GET'])
def mensajes():
    ip = obtener_ip_por_mac(ESP32_MAC)
    if not ip:
        return {"mensajes": "Dispositivo no encontrado"}
    try:
        res = requests.get(f"http://{ip}/serial?token={ESP32_TOKEN}")
        return {"mensajes": res.text if res.status_code == 200 else "Sin mensajes"}
    except Exception as e:
        return {"mensajes": f"Error: {e}"}

# === Rutas públicas para control del ESP32 desde el frontend ===

@BP_operador.route('/esp32/servo/<servo>', methods=['GET'])
def esp32_servo(servo):
    activar_servo(servo)
    return f"{servo} activado"

@BP_operador.route('/esp32/sensor/activar', methods=['GET'])
def esp32_sensor_activar():
    activar_sensor()
    return "Sensor activado"

@BP_operador.route('/esp32/sensor/desactivar', methods=['GET'])
def esp32_sensor_desactivar():
    desactivar_sensor()
    return "Sensor desactivado"

@BP_operador.route('/esp32/motor/iniciar', methods=['GET'])
def esp32_motor_iniciar():
    ip = obtener_ip_por_mac(ESP32_MAC)
    if not ip:
        return "No se pudo obtener la IP del ESP32", 404
    try:
        requests.get(f"http://{ip}/iniciar?token={ESP32_TOKEN}")
        return "Motor iniciado"
    except Exception as e:
        return f"Error al iniciar motor: {e}", 500

@BP_operador.route('/esp32/motor/detener', methods=['GET'])
def esp32_motor_detener():
    ip = obtener_ip_por_mac(ESP32_MAC)
    if not ip:
        return "No se pudo obtener la IP del ESP32", 404
    try:
        requests.get(f"http://{ip}/detener?token={ESP32_TOKEN}")
        return "Motor detenido"
    except Exception as e:
        return f"Error al detener motor: {e}", 500