"""
Pose Engine

Handles MediaPipe pose detection for the AI Fitness Tracker.

Responsibilities:
    - Load the MediaPipe Pose Landmarker model.
    - Process OpenCV camera frames.
    - Maintain frame timestamps for live/video processing.
    - Return pose landmarks for the first detected person.
    - Provide basic pose validity / visibility checks.
    - Release MediaPipe resources safely.

Designed for:
    - Live camera workouts
    - Automatic exercise detection
    - Squat / bicep curl / lunge analysis
"""

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseEngine:
    """
    MediaPipe pose detection engine optimized for live workouts.
    """

    # ==========================================================
    # DEFAULT CONFIGURATION
    # ==========================================================

    DEFAULT_MODEL_PATH = "models/pose_landmarker.task"

    DEFAULT_DETECTION_CONFIDENCE = 0.5
    DEFAULT_PRESENCE_CONFIDENCE = 0.5
    DEFAULT_TRACKING_CONFIDENCE = 0.5

    DEFAULT_NUM_POSES = 1

    # Minimum landmark visibility used by helper validation.
    DEFAULT_MIN_VISIBILITY = 0.5

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        model_path=DEFAULT_MODEL_PATH,
        detection_confidence=DEFAULT_DETECTION_CONFIDENCE,
        presence_confidence=DEFAULT_PRESENCE_CONFIDENCE,
        tracking_confidence=DEFAULT_TRACKING_CONFIDENCE,
        num_poses=DEFAULT_NUM_POSES,
        min_visibility=DEFAULT_MIN_VISIBILITY,
    ):
        """
        Create the MediaPipe Pose Landmarker.

        Parameters
        ----------
        model_path : str
            Path to pose_landmarker.task.

        detection_confidence : float
            Minimum pose detection confidence.

        presence_confidence : float
            Minimum pose presence confidence.

        tracking_confidence : float
            Minimum tracking confidence.

        num_poses : int
            Maximum number of people to detect.

        min_visibility : float
            Minimum landmark visibility used by validation helpers.
        """

        self.model_path = model_path

        self.detection_confidence = detection_confidence
        self.presence_confidence = presence_confidence
        self.tracking_confidence = tracking_confidence
        self.num_poses = num_poses
        self.min_visibility = min_visibility

        # Timestamp of the most recently processed frame.
        self.timestamp_ms = 0

        self.frame_count = 0

        self.is_closed = False

        # ------------------------------------------------------
        # MediaPipe configuration
        # ------------------------------------------------------

        base_options = python.BaseOptions(
            model_asset_path=self.model_path
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,

            # VIDEO mode is important for live camera processing.
            running_mode=vision.RunningMode.VIDEO,

            num_poses=self.num_poses,

            min_pose_detection_confidence=self.detection_confidence,
            min_pose_presence_confidence=self.presence_confidence,
            min_tracking_confidence=self.tracking_confidence,
        )

        self.detector = vision.PoseLandmarker.create_from_options(
            options
        )

    # ==========================================================
    # FRAME PROCESSING
    # ==========================================================

    def process_frame(self, frame, timestamp_ms=None):
        """
        Process one OpenCV BGR frame.

        Parameters
        ----------
        frame
            OpenCV BGR image.

        timestamp_ms : int or None
            Timestamp in milliseconds.

            If omitted, an internal monotonically increasing
            timestamp is generated.

        Returns
        -------
        MediaPipe PoseLandmarkerResult
            Detection result.
        """

        if self.is_closed:
            raise RuntimeError(
                "PoseEngine is closed. "
                "Create a new PoseEngine instance."
            )

        if frame is None:
            return None

        if not hasattr(frame, "shape"):
            raise TypeError(
                "frame must be a valid OpenCV image."
            )

        if len(frame.shape) < 2:
            raise ValueError(
                "Invalid frame dimensions."
            )

        # ------------------------------------------------------
        # Convert BGR -> RGB
        # ------------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # ------------------------------------------------------
        # Create MediaPipe image
        # ------------------------------------------------------

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # ------------------------------------------------------
        # Generate / validate timestamp
        # ------------------------------------------------------

        if timestamp_ms is None:
            # Keep timestamps strictly increasing.
            self.timestamp_ms += 1
        else:
            timestamp_ms = int(timestamp_ms)

            if timestamp_ms <= self.timestamp_ms:
                timestamp_ms = self.timestamp_ms + 1

            self.timestamp_ms = timestamp_ms

        self.frame_count += 1

        # ------------------------------------------------------
        # VIDEO mode requires timestamp
        # ------------------------------------------------------

        return self.detector.detect_for_video(
            mp_image,
            self.timestamp_ms
        )

    # ==========================================================
    # LANDMARK EXTRACTION
    # ==========================================================

    def get_landmarks(self, results):
        """
        Return landmarks for the first detected person.

        Returns
        -------
        list or None
            First person's landmarks.
        """

        if results is None:
            return None

        if not hasattr(results, "pose_landmarks"):
            return None

        if not results.pose_landmarks:
            return None

        return results.pose_landmarks[0]

    # ==========================================================
    # POSE DETECTION CHECK
    # ==========================================================

    def has_pose(self, results):
        """
        Return True if at least one person was detected.
        """

        return self.get_landmarks(results) is not None

    # ==========================================================
    # LANDMARK COUNT
    # ==========================================================

    def get_landmark_count(self, results):
        """
        Return number of landmarks detected for the first person.
        """

        landmarks = self.get_landmarks(results)

        if landmarks is None:
            return 0

        return len(landmarks)

    # ==========================================================
    # LANDMARK VISIBILITY
    # ==========================================================

    def is_landmark_visible(
        self,
        landmark,
        min_visibility=None
    ):
        """
        Check whether an individual landmark is sufficiently visible.

        MediaPipe landmarks normally expose a visibility value.
        """

        if landmark is None:
            return False

        if min_visibility is None:
            min_visibility = self.min_visibility

        visibility = getattr(
            landmark,
            "visibility",
            1.0
        )

        return visibility >= min_visibility

    # ==========================================================
    # POSE VALIDATION
    # ==========================================================

    def is_pose_valid(
        self,
        results,
        required_landmarks=None,
        min_visibility=None,
    ):
        """
        Validate whether a detected pose is usable.

        Parameters
        ----------
        results
            MediaPipe detection result.

        required_landmarks : list[int] or None
            Landmark indexes that must be visible.

        min_visibility : float or None
            Visibility threshold.

        Returns
        -------
        bool
        """

        landmarks = self.get_landmarks(results)

        if landmarks is None:
            return False

        # ------------------------------------------------------
        # Basic landmark count check
        # ------------------------------------------------------

        if len(landmarks) < 33:
            return False

        # ------------------------------------------------------
        # If no specific landmarks are required,
        # pose existence is enough.
        # ------------------------------------------------------

        if required_landmarks is None:
            return True

        if min_visibility is None:
            min_visibility = self.min_visibility

        # ------------------------------------------------------
        # Check required landmarks
        # ------------------------------------------------------

        for index in required_landmarks:

            if index < 0 or index >= len(landmarks):
                return False

            landmark = landmarks[index]

            visibility = getattr(
                landmark,
                "visibility",
                1.0
            )

            if visibility < min_visibility:
                return False

        return True

    # ==========================================================
    # FRAME INFORMATION
    # ==========================================================

    def get_frame_count(self):
        """
        Return number of processed frames.
        """

        return self.frame_count

    def get_timestamp(self):
        """
        Return the latest MediaPipe timestamp.
        """

        return self.timestamp_ms

    # ==========================================================
    # RESET TRACKING
    # ==========================================================

    def reset(self):
        """
        Reset internal frame/timestamp counters.

        Note:
            MediaPipe's detector itself remains alive.
        """

        self.timestamp_ms = 0
        self.frame_count = 0

    # ==========================================================
    # RESOURCE CLEANUP
    # ==========================================================

    def close(self):
        """
        Release MediaPipe resources safely.
        """

        if self.is_closed:
            return

        if self.detector is not None:
            self.detector.close()

        self.is_closed = True

    # ==========================================================
    # CONTEXT MANAGER SUPPORT
    # ==========================================================

    def __enter__(self):
        """
        Allow:

            with PoseEngine() as pose:
                ...
        """

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        """
        Automatically release resources.
        """

        self.close()