"""
Live Automatic Workout

Complete pipeline:

    Webcam
       ↓
    MediaPipe PoseEngine
       ↓
    Landmark Validation
       ↓
    WorkoutEngine.process_auto()
       ↓
    Exercise Detection
       ↓
    Exercise Analyzer
       ↓
    Standard Workout Result
       ↓
    VoiceController
       ↓
    SpeechQueue
       ↓
    SpeechWorker
       ↓
    Speaker
"""

import cv2

from ai_engine.pose_engine import PoseEngine
from ai_engine.workout.workout_engine import WorkoutEngine

from voice_engine.speech_queue import SpeechQueue
from voice_engine.speech_worker import SpeechWorker
from voice_engine.voice_controller import VoiceController


class LiveAutoWorkout:

    def __init__(
        self,
        camera_index=0,
        model_path="models/pose_landmarker.task",
        voice_enabled=True,
        voice_confidence=0.70,
        speech_rate=175,
        speech_volume=1.0,
        speech_queue_size=20,
    ):

        self.camera_index = camera_index
        self.model_path = model_path

        self.camera = None

        # ------------------------------------------------------
        # AI
        # ------------------------------------------------------

        self.pose_engine = PoseEngine(
            model_path=model_path
        )

        self.workout_engine = WorkoutEngine()

        # ------------------------------------------------------
        # Voice
        # ------------------------------------------------------

        self.voice_enabled = bool(
            voice_enabled
        )

        self.speech_queue = None
        self.speech_worker = None
        self.voice_controller = None

        if self.voice_enabled:

            self.speech_queue = SpeechQueue(
                max_size=speech_queue_size
            )

            self.speech_worker = SpeechWorker(
                self.speech_queue,
                rate=speech_rate,
                volume=speech_volume,
            )

            self.voice_controller = VoiceController(
                self.speech_queue,
                min_confidence=voice_confidence,
            )

        # ------------------------------------------------------
        # State
        # ------------------------------------------------------

        self.running = False

        self.last_result = (
            self._waiting_result()
        )

    # ==========================================================
    # START
    # ==========================================================

    def start(self):

        if self.running:
            return True

        self.camera = cv2.VideoCapture(
            self.camera_index
        )

        if not self.camera.isOpened():

            self.camera.release()
            self.camera = None

            raise RuntimeError(
                "Unable to open webcam."
            )

        # Start automatic workout detection.
        self.workout_engine.start_auto()

        # Start speech worker before processing frames.
        if (
            self.voice_enabled
            and self.speech_worker is not None
        ):

            self.speech_worker.start()

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):

            self.voice_controller.announce_workout_started()

        self.running = True

        return True

    # ==========================================================
    # PROCESS FRAME
    # ==========================================================

    def process_frame(self, frame):

        if self.pose_engine is None:
            raise RuntimeError(
                "Pose engine is not initialized."
            )

        if self.workout_engine is None:
            raise RuntimeError(
                "Workout engine is not initialized."
            )

        # ------------------------------------------------------
        # Empty frame
        # ------------------------------------------------------

        if frame is None:

            return self._set_result(
                self._waiting_result()
            )

        # ------------------------------------------------------
        # Frame validation
        # ------------------------------------------------------

        if not hasattr(frame, "shape"):

            return self._set_result(
                self._waiting_result()
            )

        if len(frame.shape) != 3:

            return self._set_result(
                self._waiting_result()
            )

        height, width = frame.shape[:2]

        if height <= 0 or width <= 0:

            return self._set_result(
                self._waiting_result()
            )

        # ------------------------------------------------------
        # MediaPipe
        # ------------------------------------------------------

        try:

            pose_results = (
                self.pose_engine.process_frame(
                    frame
                )
            )

        except Exception as error:

            print(
                f"Pose processing error: {error}"
            )

            return self._set_result(
                self._waiting_result()
            )

        if pose_results is None:

            return self._set_result(
                self._waiting_result()
            )

        # ------------------------------------------------------
        # Landmarks
        # ------------------------------------------------------

        try:

            landmarks = (
                self.pose_engine.get_landmarks(
                    pose_results
                )
            )

        except Exception as error:

            print(
                f"Landmark extraction error: {error}"
            )

            return self._set_result(
                self._waiting_result()
            )

        if landmarks is None:

            return self._set_result(
                self._waiting_result()
            )

        # ------------------------------------------------------
        # Landmark count
        # ------------------------------------------------------

        if len(landmarks) < 33:

            return self._set_result(
                self._waiting_result()
            )

        # ------------------------------------------------------
        # Required landmarks
        # ------------------------------------------------------

        required_indexes = [
            11, 12,       # shoulders
            13, 14,       # elbows
            15, 16,       # wrists
            23, 24,       # hips
            25, 26,       # knees
            27, 28,       # ankles
        ]

        for index in required_indexes:

            landmark = landmarks[index]

            if landmark is None:

                return self._set_result(
                    self._waiting_result()
                )

            if not hasattr(
                landmark,
                "x",
            ):

                return self._set_result(
                    self._waiting_result()
                )

            if not hasattr(
                landmark,
                "y",
            ):

                return self._set_result(
                    self._waiting_result()
                )

        # ------------------------------------------------------
        # Workout engine
        # ------------------------------------------------------

        try:

            result = (
                self.workout_engine.process_auto(
                    landmarks
                )
            )

        except RuntimeError:

            result = self._waiting_result()

        except Exception as error:

            print(
                f"Workout processing error: {error}"
            )

            result = self._waiting_result()

        # ------------------------------------------------------
        # Normalize result
        # ------------------------------------------------------

        result = self._normalize_result(
            result
        )

        self.last_result = result

        # ------------------------------------------------------
        # Voice
        # ------------------------------------------------------

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):

            try:

                self.voice_controller.process(
                    result
                )

            except Exception as error:

                print(
                    f"Voice controller error: {error}"
                )

        return result

    # ==========================================================
    # NORMALIZE RESULT
    # ==========================================================

    @staticmethod
    def _normalize_result(result):

        if not isinstance(result, dict):

            return {
                "exercise": None,
                "detected_exercise": None,
                "confidence": 0.0,
                "side": None,
                "status": "waiting",
                "reps": 0,
                "state": None,
                "form": None,
                "detection_mode": "automatic",
            }

        exercise = result.get(
            "exercise"
        )

        detected_exercise = result.get(
            "detected_exercise",
            exercise,
        )

        confidence = result.get(
            "confidence",
            0.0,
        )

        # ------------------------------------------------------
        # Safe confidence
        # ------------------------------------------------------

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # ------------------------------------------------------
        # Safe reps
        # ------------------------------------------------------

        try:

            reps = int(
                result.get(
                    "reps",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            reps = 0

        reps = max(
            0,
            reps,
        )

        # ------------------------------------------------------
        # Status
        # ------------------------------------------------------

        status = result.get(
            "status"
        )

        if status is None:

            status = (
                "active"
                if exercise
                else "waiting"
            )

        # ------------------------------------------------------
        # Normalized result
        # ------------------------------------------------------

        return {
            "exercise": exercise,

            "detected_exercise": (
                detected_exercise
            ),

            "confidence": confidence,

            "side": result.get(
                "side"
            ),

            "status": status,

            "reps": reps,

            "state": result.get(
                "state"
            ),

            "form": result.get(
                "form"
            ),

            "detection_mode": result.get(
                "detection_mode",
                "automatic",
            ),
        }

    # ==========================================================
    # WAITING RESULT
    # ==========================================================

    def _waiting_result(self):

        return {
            "exercise": None,
            "detected_exercise": None,
            "confidence": 0.0,
            "side": None,

            # Important:
            # The live test expects "waiting".
            "status": "waiting",

            "reps": 0,
            "state": None,
            "form": None,
            "detection_mode": "automatic",
        }

    # ==========================================================
    # SET RESULT
    # ==========================================================

    def _set_result(self, result):

        result = self._normalize_result(
            result
        )

        self.last_result = result

        # Send waiting / fallback results
        # through the voice controller too.
        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):

            try:

                self.voice_controller.process(
                    result
                )

            except Exception as error:

                print(
                    f"Voice controller error: {error}"
                )

        return result

    # ==========================================================
    # GET RESULT
    # ==========================================================

    def get_result(self):

        return self.last_result

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        self.start()

        print()
        print(
            "AI FITNESS TRACKER"
        )
        print(
            "------------------"
        )
        print(
            "Camera              : OK"
        )
        print(
            "Automatic detection : ENABLED"
        )
        print(
            "Voice               : "
            f"{'ENABLED' if self.voice_enabled else 'DISABLED'}"
        )
        print()

        print(
            "Stand clearly in front of the camera."
        )

        print(
            "Perform one exercise at a time."
        )

        print()

        print(
            "Q = Quit"
        )

        print(
            "R = Reset"
        )

        print()

        try:

            while self.running:

                success, frame = (
                    self.camera.read()
                )

                if not success:

                    print(
                        "Warning: unable to read camera frame."
                    )

                    continue

                # ------------------------------------------------
                # Mirror view
                # ------------------------------------------------

                frame = cv2.flip(
                    frame,
                    1,
                )

                # ------------------------------------------------
                # AI
                # ------------------------------------------------

                result = self.process_frame(
                    frame
                )

                # ------------------------------------------------
                # UI
                # ------------------------------------------------

                self._draw_status(
                    frame,
                    result,
                )

                cv2.imshow(
                    "AI Fitness Tracker",
                    frame,
                )

                key = (
                    cv2.waitKey(1)
                    & 0xFF
                )

                if key == ord("q"):

                    break

                if key == ord("r"):

                    self.reset()

        finally:

            self.stop()

    # ==========================================================
    # DRAW STATUS
    # ==========================================================

    def _draw_status(
        self,
        frame,
        result,
    ):

        exercise = result.get(
            "exercise"
        )

        reps = result.get(
            "reps",
            0,
        )

        confidence = result.get(
            "confidence",
            0.0,
        )

        status = result.get(
            "status",
            "waiting",
        )

        side = result.get(
            "side"
        )

        form = result.get(
            "form"
        )

        # ------------------------------------------------------
        # Exercise text
        # ------------------------------------------------------

        if exercise:

            exercise_text = (
                str(exercise)
                .replace("_", " ")
                .title()
            )

        else:

            exercise_text = (
                "Waiting..."
            )

        # ------------------------------------------------------
        # Exercise
        # ------------------------------------------------------

        cv2.putText(
            frame,
            f"Exercise: {exercise_text}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        # ------------------------------------------------------
        # Reps
        # ------------------------------------------------------

        cv2.putText(
            frame,
            f"Reps: {reps}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        # ------------------------------------------------------
        # Confidence
        # ------------------------------------------------------

        cv2.putText(
            frame,
            f"Confidence: {confidence:.2f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        # ------------------------------------------------------
        # Status
        # ------------------------------------------------------

        cv2.putText(
            frame,
            f"Status: {status}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        # ------------------------------------------------------
        # Side
        # ------------------------------------------------------

        if side:

            cv2.putText(
                frame,
                f"Side: {side}",
                (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                (255, 255, 255),
                2,
            )

        # ------------------------------------------------------
        # Form
        # ------------------------------------------------------

        if form:

            form_text = str(
                form
            )[:60]

            cv2.putText(
                frame,
                f"Form: {form_text}",
                (20, 215),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        if self.workout_engine is not None:

            self.workout_engine.reset()

        if self.voice_controller is not None:

            self.voice_controller.reset()

            try:

                self.voice_controller.announce_workout_reset()

            except Exception as error:

                print(
                    f"Voice reset error: {error}"
                )

        if self.speech_worker is not None:

            try:

                # Remove stale rep/form announcements.
                self.speech_worker.clear_queue()

            except Exception as error:

                print(
                    f"Speech queue clear error: {error}"
                )

        self.last_result = (
            self._waiting_result()
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        # ------------------------------------------------------
        # Always release camera if it exists.
        # ------------------------------------------------------

        if self.camera is not None:

            try:
                self.camera.release()
            except Exception:
                pass

            self.camera = None

        was_running = self.running

        self.running = False

        # ------------------------------------------------------
        # Stop announcement
        # ------------------------------------------------------

        if (
            was_running
            and self.voice_enabled
            and self.voice_controller is not None
        ):

            try:

                self.voice_controller.announce_workout_stopped()

            except Exception:
                pass

        # ------------------------------------------------------
        # Workout
        # ------------------------------------------------------

        if self.workout_engine is not None:

            try:

                self.workout_engine.stop()

            except Exception:
                pass

        # ------------------------------------------------------
        # Speech
        # ------------------------------------------------------

        if self.speech_worker is not None:

            try:

                self.speech_worker.stop()

            except Exception:
                pass

        # ------------------------------------------------------
        # OpenCV
        # ------------------------------------------------------

        try:

            cv2.destroyAllWindows()

        except Exception:
            pass

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):

        self.stop()

        if self.pose_engine is not None:

            try:

                self.pose_engine.close()

            except Exception:
                pass

            self.pose_engine = None