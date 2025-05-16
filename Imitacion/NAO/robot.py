import os
import sys
import time
os.environ['GLOG_minloglevel'] = '3'  
import cv2
import mediapipe as mp
import numpy as np
import socket
import json
sys.path.append('..')
from computerVisionModules import head, elbows, Landmarks
from outputModule import output

# Configuración de constantes
ANGLE_TYPE = "Degree"
TARGET_FPS = 30
SOCKET_TIMEOUT = 2.0

class VisionSystem:
    def __init__(self):
        self.cap = None
        self.face_mesh = None
        self.pose = None
        self.client_socket = None
        self.last_frame_time = 0
        self.program_output = output.Output()
        self.landmark_handler = Landmarks.Landmarks()
        self.elbows_processor = elbows.Elbows()
        
        # Configuración inicial
        self.interface_inputs = {
            "Head": True,
            "HeadText": True,
            "Elbows": True,
            "ElbowsText": True,
            "DrawSkeleton": True,
            "BlackBackground": False
        }

    def init_camera(self):
        """Inicializa la cámara con múltiples intentos y backends"""
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_V4L2, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
                print(f"Cámara inicializada con backend: {backend}")
                return cap
        
        print("Error: No se pudo inicializar la cámara con ningún backend")
        return None

    def connect_to_nao(self, ip='127.0.0.1', port=65432):
        """Establece conexión con el robot NAO"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(SOCKET_TIMEOUT)
            self.client_socket.connect((ip, port))
            print("Conectado al robot NAO")
            return True
        except Exception as e:
            print(f"Error de conexión con NAO: {str(e)}")
            self.client_socket = None
            return False

    def process_frame(self, frame):
        """Procesa un frame y devuelve los resultados"""
        try:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            # Detección de landmarks
            face_results = self.face_mesh.process(image)
            body_results = self.pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Procesamiento de cabeza
            if (self.interface_inputs["Head"] and 
                face_results.multi_face_landmarks):
                head_angle = head.get_head_positions(
                    image, face_results, ANGLE_TYPE,
                    show_text=self.interface_inputs["HeadText"]
                )
                self.program_output.output["Angles"]["Head"] = head_angle
            
            # Procesamiento de codos
            if (self.interface_inputs["Elbows"] and 
                body_results.pose_landmarks):
                body_info = self.landmark_handler.get_body_landmarks_info(body_results, image)
                elbows_angle = self.elbows_processor.get_elbows_info(
                    image, body_info, ANGLE_TYPE,
                    show_text=self.interface_inputs["ElbowsText"]
                )
                self.program_output.output["Angles"]["Elbows"] = elbows_angle
                
                if self.interface_inputs["DrawSkeleton"]:
                    mp.solutions.drawing_utils.draw_landmarks(
                        image, body_results.pose_landmarks, 
                        mp.solutions.pose.POSE_CONNECTIONS,
                        mp.solutions.drawing_utils.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                        mp.solutions.drawing_utils.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                    )
            
            return image, self.program_output.output
        
        except Exception as e:
            print(f"Error en procesamiento: {str(e)}")
            return frame, None

    def send_to_nao(self, data):
        """Envía datos al NAO con manejo de errores"""
        if not self.client_socket:
            return False
            
        try:
            self.client_socket.sendall((json.dumps(data) + "\n").encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error en envío de datos: {str(e)}")
            self.client_socket = None
            return False

    def run(self):
        """Bucle principal del sistema de visión"""
        # Inicializar modelos
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_faces=1
        )
        
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Inicializar cámara
        self.cap = self.init_camera()
        if not self.cap or not self.cap.isOpened():
            print("Error crítico: No se pudo inicializar la cámara")
            return
        
        # Conectar con NAO (opcional)
        self.connect_to_nao()
        
        # Bucle principal
        while True:
            # Control de FPS
            current_time = time.time()
            elapsed = current_time - self.last_frame_time
            if elapsed < 1.0/TARGET_FPS:
                time.sleep((1.0/TARGET_FPS) - elapsed)
            self.last_frame_time = current_time
            
            # Capturar frame
            ret, frame = self.cap.read()
            if not ret:
                print("Error: No se pudo capturar frame")
                break
            
            # Procesar frame
            processed_frame, angles = self.process_frame(frame)
            
            # Mostrar resultados
            cv2.imshow("NAO Robot - Seguimiento Postural", processed_frame)
            
            # Enviar datos al NAO
            if angles and self.client_socket:
                self.send_to_nao(angles)
            
            # Salir con 'Q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Liberar recursos
        self.cap.release()
        cv2.destroyAllWindows()
        if self.client_socket:
            self.client_socket.close()
        self.face_mesh.close()
        self.pose.close()

if __name__ == "__main__":
    vision_system = VisionSystem()
    vision_system.run()