import numpy as np
import cv2
from computerVisionModules import bodyComponents 

class Utils:
    def __init__(self, filter_on=True, filter_deviation=5, filter_difference=30, filter_frame_number=5):
        self.landmarks_name_id_dict = bodyComponents.BODY_LANDMARKS
        self.previous_frames_angles = {"Left": [], "Right": []}
        self.filter_deviation = filter_deviation
        self.filter_difference = filter_difference
        self.filter_frame_number = filter_frame_number
        self.filter_on = filter_on
        self.Z_MAGNITUDE = 2.5
        self.VISIBILITY_THRESHOLD = 0.5  # Umbral de visibilidad (0-1)

    def visualize_text(self, image, coordinate, text="No text", color=(250, 250, 250),
                   size=1, thickness=2, font=cv2.FONT_HERSHEY_SIMPLEX, lineType=cv2.LINE_AA):
        coordinate = (int(coordinate[0]), int(coordinate[1]))  # ✅ forzar enteros
        cv2.putText(image, text, coordinate, font, size, color, thickness, lineType)


    def get_coordinate_of_point(self, landmark_point, image):
        """Convierte landmarks normalizados a coordenadas de imagen con profundidad estimada"""
        x = landmark_point[0] * image.shape[1]
        y = landmark_point[1] * image.shape[0]
        z = landmark_point[2] * image.shape[1]/self.Z_MAGNITUDE
        return (x, y, z)

    def is_points_visible(self, points):
        """Verifica si los puntos son visibles según su score de confianza"""
        return all(point[3] > self.VISIBILITY_THRESHOLD for point in points)

    def get_angle(self, points, image, dimension="3D", side="Left"):
        """Calcula el ángulo entre tres puntos en 3D (o 2D si se especifica)
        
        Args:
            points: Tupla de 3 puntos de landmarks
            image: Imagen numpy array para obtener dimensiones
            dimension: "3D" o "2D" para tipo de cálculo
            side: "Left" o "Right" para filtrado independiente
        """
        if not self.is_points_visible(points):
            print("Aviso: Puntos no visibles para cálculo de ángulo preciso")
            return None

        p1, p2, p3 = points
        coord_p1 = self.get_coordinate_of_point(p1, image)
        coord_p2 = self.get_coordinate_of_point(p2, image)
        coord_p3 = self.get_coordinate_of_point(p3, image)

        if dimension == "3D":
            degree = self.calculate_3d_angle(coord_p1, coord_p2, coord_p3)
        else:
            points_2d = self.get_dimension_axis(coord_p1, coord_p2, coord_p3, dimension)
            degree, _ = self.calculate_2d_angle(points_2d)

        if self.filter_on:
            degree = self.apply_angle_filter(degree, side)

        return {
            "Degree": degree,
            "Radian": np.deg2rad(degree)
        }

    # Resto de los métodos permanecen igual...
    # calculate_3d_angle, calculate_2d_angle, apply_angle_filter, etc.
    def calculate_3d_angle(self, a, b, c):
        """Calcula el ángulo entre tres puntos en espacio 3D"""
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1, 1)))
        return angle

    def calculate_2d_angle(self, points):
        """Mantiene tu método original para compatibilidad"""
        point1, point2, point3 = points
        value1 = np.arctan2(point3[1] - point2[1], point3[0] - point2[0])
        value2 = np.arctan2(point1[1] - point2[1], point1[0] - point2[0])
        radian = value1 - value2

        if radian > np.pi:
            radian = 2*np.pi - radian

        return np.degrees(radian), radian

    def apply_angle_filter(self, angle, side):
        """Filtro mejorado con media móvil ponderada"""
        if side not in self.previous_frames_angles:
            return angle
            
        frames = self.previous_frames_angles[side]
        frames.append(angle)
        
        if len(frames) > self.filter_frame_number:
            frames.pop(0)
        
        # Media ponderada (más peso a valores recientes)
        weights = np.linspace(1, 2, len(frames))
        filtered = np.average(frames, weights=weights)
        
        # Solo aplicar si no hay cambio brusco
        if abs(angle - filtered) < self.filter_difference:
            if abs(angle - filtered) > self.filter_deviation:
                return filtered
                
        return angle