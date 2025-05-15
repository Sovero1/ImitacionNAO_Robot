# -*- coding: utf-8 -*-

import socket
import json
from naoqi import ALProxy

# Dirección IP del robot NAO
ROBOT_IP = "localhost"  # ip 
ROBOT_PORT = 56588

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

def mover_codos_nao(motion_proxy, angles):
    def clamp(value, min_val, max_val):
        return max(min(value, max_val), min_val)

    # Obtener ángulos de los codos
    left_elbow = get_joint_value(angles, ["Angles", "Elbows", "Left", "Roll"])
    right_elbow = get_joint_value(angles, ["Angles", "Elbows", "Right", "Roll"])

    if left_elbow is not None and right_elbow is not None:
        # Convertir a radianes si vienen en grados
        if abs(left_elbow) > np.pi * 2:
            left_elbow = np.radians(left_elbow)
        if abs(right_elbow) > np.pi * 2:
            right_elbow = np.radians(right_elbow)

        # Rango real del NAO
        LEFT_MIN, LEFT_MAX = -1.54, -0.03
        RIGHT_MIN, RIGHT_MAX = 0.03, 1.54

        # Normalizar los ángulos al rango 0 - π
        left_norm = np.clip(left_elbow, 0, np.pi) / np.pi
        right_norm = np.clip(right_elbow, 0, np.pi) / np.pi

        # Mapear al rango del NAO
        left_value = LEFT_MIN + left_norm * (LEFT_MAX - LEFT_MIN)
        right_value = RIGHT_MIN + right_norm * (RIGHT_MAX - RIGHT_MIN)

        # Protección adicional
        left_value = clamp(left_value, LEFT_MIN, LEFT_MAX)
        right_value = clamp(right_value, RIGHT_MIN, RIGHT_MAX)

        names = ["LElbowRoll", "RElbowRoll"]
        values = [left_value, right_value]
        speed = 0.2
        motion_proxy.setAngles(names, values, speed)

        print(u" Moviendo codos: Izq={:.2f}° ({:.3f} rad), Der={:.2f}° ({:.3f} rad)".format(
            np.degrees(left_elbow), left_value, np.degrees(right_elbow), right_value))

    else:
        print(u"No se puede mover los codos por valores nulos.")

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
        print(" Esperando conexión del sistema de visión...")
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