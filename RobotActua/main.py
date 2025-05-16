# -*- coding: utf-8 -*-

import socket
import json
from naoqi import ALProxy

# Dirección IP del robot NAO
ROBOT_IP = "localhost"  # ip 
ROBOT_PORT = 54403

# Dirección del servidor socket
HOST = '127.0.0.1'
PORT = 65432

def get_joint_value(data, path_list, angle_type="Radian"):
    try:
        ref = data
        for key in path_list:
            ref = ref[key]
        value = ref.get(angle_type)
        if value is None:
            print(u" Valor nulo: " + " -> ".join(path_list) + " [" + angle_type + "]")
        return value
    except (KeyError, TypeError) as e:
        print(u" Error extrayendo {}: {}".format(" -> ".join(path_list), str(e)))
        return None

def mover_cabeza_nao(motion_proxy, angles):
    pitch = get_joint_value(angles, ["Angles", "Head", "Pitch"])
    yaw = get_joint_value(angles, ["Angles", "Head", "Yaw"])
    
    if pitch is not None and yaw is not None:
        names = ["HeadPitch", "HeadYaw"]
        values = [-pitch, yaw]  # El NAO mueve el Pitch de manera opuesta
        speed = 0.2  # Velocidad de movimiento
        motion_proxy.setAngles(names, values, speed)
        print(u" Moviendo cabeza: Pitch={}, Yaw={}".format(pitch, yaw))
    else:
        print(u"No se puede mover la cabeza por valores nulos.")

def mover_codos_nao(motion_proxy, angles, speed=0.2, verbose=True):
    """Versión compatible con Python 2.7"""
    def clamp(value, min_val, max_val):
        return max(min(value, max_val), min_val)

    # Rangos reales del NAO (en radianes)
    NAO_RANGES = {
        "Left": (-1.54, -0.03),  # LElbowRoll
        "Right": (0.03, 1.54)     # RElbowRoll
    }

    # Compatibilidad con ambas estructuras (antigua y nueva)
    try:
        left_roll = angles.get("Angles", {}).get("Elbows", {}).get("Left", {}).get("Roll", {})
        right_roll = angles.get("Angles", {}).get("Elbows", {}).get("Right", {}).get("Roll", {})
        
        left_angle = left_roll.get("Radian")
        right_angle = right_roll.get("Radian")
    except AttributeError:
        left_angle = right_angle = None

    if left_angle is None or right_angle is None:
        if verbose:
            print("Advertencia: Angulos de codos no validos")
        return False

    try:
        # Mapeo invertido para el codo izquierdo
        left_min, left_max = NAO_RANGES["Left"]
        right_min, right_max = NAO_RANGES["Right"]
        
        left_value = clamp(-left_angle, left_min, left_max)
        right_value = clamp(right_angle, right_min, right_max)

        # Configurar movimiento
        names = ["LElbowRoll", "RElbowRoll"]
        speed = clamp(speed, 0.1, 1.0)
        motion_proxy.setAngles(names, [left_value, right_value], speed)

        if verbose:
            print(u"Movimiento codos NAO - L: {:.1f}° ({:.3f} rad), R: {:.1f}° ({:.3f} rad)".format(
                np.degrees(left_angle), left_value,
                np.degrees(right_angle), right_value))
        
        return True

    except Exception as e:
        print("Error al mover codos: {}".format(str(e)))
        return False
    
def main():
    try:
        motion = ALProxy("ALMotion", ROBOT_IP, ROBOT_PORT)
        motion.setStiffnesses("Body", 1.0)  # Activar rigidez para poder mover
        print(u" Conectado a NAO")
    except Exception as e:
        print(" No se pudo conectar a NAO:", str(e))
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
        s.listen(1)
        print(" Esperando conexión del sistema de vision...")
        conn, addr = s.accept()
        print(" Conectado por {}".format(addr))

        buffer = ""
        while True:
            data = conn.recv(1024)
            if not data:
                break

            buffer += data.decode("utf-8")
            try:
                json_data = json.loads(buffer)
                mover_cabeza_nao(motion, json_data)
                mover_codos_nao(motion, json_data)  # Nueva función para codos
                buffer = ""
            except ValueError:
                continue  # JSON incompleto, seguir esperando

    finally:
        motion.setStiffnesses("Body", 0.0)  # Relajar los motores al terminar
        s.close()

if __name__ == "__main__":
    import numpy as np  # Necesario para las conversiones de ángulos
    main()