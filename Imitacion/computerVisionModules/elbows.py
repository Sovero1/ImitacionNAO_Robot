from computerVisionModules.Utils import Utils  # Importa la clase específica

import numpy as np

class Elbows(Utils):
    def __init__(self):
        super().__init__()
        self.elbows = ["left_elbow", "right_elbow"]
        self.joint_combinations = {
            13: (11, 13, 15),  # left_elbow: (left_shoulder, left_elbow, left_wrist)
            14: (12, 14, 16)   # right_elbow: (right_shoulder, right_elbow, right_wrist)
        }
        # Estructura compatible con mover_codos_nao
        self.elbows_output = {
            "Angles": {
                "Elbows": {
                    "Left": {"Roll": {"Degree": 180, "Radian": np.pi}},
                    "Right": {"Roll": {"Degree": 180, "Radian": np.pi}}
                }
            }
        }
        self.textColor = (250, 250, 250)

    def get_elbows_info(self, image, body_landmarks, angle_type="Degree", show_text=True):
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
          self.visualize_text(image, (int(x + offset), int(y)), text, self.textColor)

        for elbow in self.elbows:
            elbow_id = self.landmarks_name_id_dict[elbow]
            p1, p2, p3 = self.joint_combinations[elbow_id]
            points = (body_landmarks[p1], body_landmarks[p2], body_landmarks[p3])

            x = int(body_landmarks[elbow_id][0] * image.shape[1])
            y = int(body_landmarks[elbow_id][1] * image.shape[0])

            side = "Left" if elbow == "left_elbow" else "Right"
            angle_data = self.get_angle(points, image, dimension="3D", side=side)
            
            if angle_data:
                self.elbows_output["Angles"]["Elbows"][side]["Roll"] = angle_data

                if show_text:
                    text = f"({abs(angle_data[angle_type]):.1f})"
                    offset = 20 if side == "Left" else -100
                    self.visualize_text(image, (x+offset, y), text, self.textColor)

        return self.elbows_output