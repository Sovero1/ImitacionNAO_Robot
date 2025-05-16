# Landmarks.py
from computerVisionModules import Utils

class Landmarks(Utils.Utils):
    def __init__(self):
        super().__init__()
        self.body_landmarks_info = {}

    def get_body_landmarks_info(self, results, image):
        for id, landmark in enumerate(results.pose_landmarks.landmark):
            x = landmark.x
            y = landmark.y
            z = landmark.z
            visibility = landmark.visibility  

            coordinates = self.get_coordinate_of_point((x, y, z), image)
            self.body_landmarks_info[id] = coordinates + (visibility,)

        return self.body_landmarks_info
