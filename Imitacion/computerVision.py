import cv2
import mediapipe as mp
import numpy as np
from computerVisionModules import elbows, head, Landmarks
from outputModule import output

# Inicialización de modelos MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_face_mesh = mp.solutions.face_mesh

# Configuración de modelos
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_faces=1)  # Solo detectar una cara

pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Instancias de módulos propios
elbows_processor = elbows.Elbows()
head_processor = head  # Módulo con función get_head_positions()
landmark_handler = Landmarks.Landmarks()
program_output = output.Output()

ANGLE_TYPE = "Degree"

def run_computer_vision(frame):
    # Convertir la imagen a RGB
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    
    # Detección de landmarks
    face_results = face_mesh.process(image)
    body_results = pose.process(image)
    
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    if not body_results.pose_landmarks:
        cv2.putText(image, "No se detecto cuerpo", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return image
    
    # Obtener info de landmarks para cálculo de ángulos
    body_info = landmark_handler.get_body_landmarks_info(body_results, image)
    
    # Calcular ángulo de cabeza
    head_angle = {"Pitch": {"Degree": 0, "Radian": 0},
                  "Roll": {"Degree": 0, "Radian": 0},
                  "Yaw": {"Degree": 0, "Radian": 0}}
    
    if face_results.multi_face_landmarks:
        head_angle = head_processor.get_head_positions(image, face_results, ANGLE_TYPE, show_text=True)
    
    # Calcular ángulos de codos
    elbows_angle = elbows_processor.get_elbows_info(image, body_info, ANGLE_TYPE, show_text=True)
    
    # Actualizar salida
    program_output.output["Angles"]["Head"] = head_angle
    program_output.output["Angles"]["Elbows"] = elbows_angle
    
    # Dibujar esqueleto
    mp_drawing.draw_landmarks(
        image, body_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
        mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
    )
    
    # Guardar resultados en JSON (puedes reducir la frecuencia para mejor rendimiento)
    program_output.write_json_data("./output.json")
    
    return image

# Configuración de la cámara
cap = cv2.VideoCapture(0)  # 0 para cámara predeterminada

# Configurar tamaño del frame (opcional)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("No se pudo obtener frame de la cámara")
        break
    
    # Procesar frame
    processed_frame = run_computer_vision(frame)
    
    # Mostrar resultado
    cv2.imshow('Seguimiento Postural', processed_frame)
    
    # Salir con 'q' o ESC
    key = cv2.waitKey(1)
    if key == ord('q') or key == 27:  # 27 es ESC
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()