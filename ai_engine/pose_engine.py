import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseEngine:
    def __init__(self, model_path="models/pose_landmarker.task"):
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.detector = vision.PoseLandmarker.create_from_options(
            options
        )

    def process_frame(self, frame):
        """
        Process an OpenCV BGR frame with MediaPipe.
        """

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        return self.detector.detect(mp_image)

    def get_landmarks(self, results):
        """
        Return the landmarks for the first detected person.
        """

        if not results.pose_landmarks:
            return None

        return results.pose_landmarks[0]

    def close(self):
        """
        Release MediaPipe resources.
        """

        self.detector.close()