import os
import sys
os.environ['GLOG_minloglevel'] = '3'  
import cv2
import mediapipe as mp
import numpy as np
import socket
import json
sys.path.append('..')  # Añadir la carpeta superior
from computerVisionModules import head, elbows, Landmarks
from outputModule import output

# 1. Configuración inicial de la cámara
def init_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Forzar backend DSHOW en Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap

# 2. Inicialización de modelos
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_face_mesh = mp.solutions.face_mesh

# 3. Función principal de procesamiento
def run_computer_vision(frame, interface_inputs):
    try:
        # Convertir y procesar frame
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # Detección de landmarks
        face_results = face_mesh.process(image)
        body_results = pose.process(image)
        
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Procesamiento de cabeza
        if interface_inputs["Head"] and face_results.multi_face_landmarks:
            head_angle = head.get_head_positions(
                image, face_results, ANGLE_TYPE,
                show_text=interface_inputs["HeadText"]
            )
            program_output.output["Angles"]["Head"] = head_angle
        
        # Procesamiento de codos
        if interface_inputs["Elbows"] and body_results.pose_landmarks:
            body_info = landmark_handler.get_body_landmarks_info(body_results, image)
            elbows_angle = elbows_processor.get_elbows_info(
                image, body_info, ANGLE_TYPE,
                show_text=interface_inputs["ElbowsText"]
            )
            program_output.output["Angles"]["Elbows"] = elbows_angle
            
            if interface_inputs["DrawSkeleton"]:
                mp_drawing.draw_landmarks(
                    image, body_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                )
        
        return image
    
    except Exception as e:
        print(f"Error en procesamiento: {str(e)}")
        return frame

# 4. Configuración principal
if __name__ == "__main__":
    # Inicializar modelos
    face_mesh = mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_faces=1
    )
    
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Nuestros módulos
    program_output = output.Output()
    landmark_handler = Landmarks.Landmarks()
    elbows_processor = elbows.Elbows()
    
    ANGLE_TYPE = "Degree"
    
    # Conexión con NAO (con manejo de errores)
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 65432))
        print("Conectado al robot NAO")
    except Exception as e:
        print(f"Error de conexión con NAO: {str(e)}")
        client_socket = None
    
    # Interfaz de control
    interface_inputs = {
        "Head": True,
        "HeadText": True,
        "Elbows": True,
        "ElbowsText": True,
        "DrawSkeleton": True,
        "BlackBackground": False
    }
    
    # Iniciar cámara
    cap = init_camera() 
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        exit()
    
    # Bucle principal
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar frame")
            break
        
        processed_frame = run_computer_vision(frame, interface_inputs)
        cv2.imshow("NAO Robot - Seguimiento Postural", processed_frame)
        
        # Envío de datos (si hay conexión)
        if client_socket:
            try:
                client_socket.sendall(
                    (json.dumps(program_output.output) + "\n").encode('utf-8')
                )
            except Exception as e:
                print(f"Error en envío de datos: {str(e)}")
                client_socket = None
        
        # Salir con 'Q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    if client_socket:
        client_socket.close()