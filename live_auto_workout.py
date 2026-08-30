"""
Live Automatic Workout
======================

Complete production pipeline:

    Webcam
       ↓
    MediaPipe PoseEngine
       ↓
    Landmark Validation
       ↓
    WorkoutEngine.process_auto()
       ↓
    Stable Exercise Detection
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

        # ======================================================
        # AI
        # ======================================================

        self.pose_engine = PoseEngine(
            model_path=model_path
        )

        self.workout_engine = WorkoutEngine()

        # ======================================================
        # VOICE
        # ======================================================

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

        # ======================================================
        # STATE
        # ======================================================

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

        # ------------------------------------------------------
        # Automatic workout.
        # ------------------------------------------------------

        self.workout_engine.start_auto()

        # ------------------------------------------------------
        # Speech worker MUST start before events are queued.
        # ------------------------------------------------------

        if (
            self.voice_enabled
            and self.speech_worker is not None
        ):

            self.speech_worker.start()

        self.running = True

        # ------------------------------------------------------
        # Announce workout.
        # ------------------------------------------------------

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):

            self.voice_controller.announce_workout_started()

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
        # Frame validation.
        # ------------------------------------------------------

        if frame is None:
            return self._set_result(
                self._waiting_result()
            )

        if not hasattr(
            frame,
            "shape",
        ):
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

        # ======================================================
        # MEDIAPIPE
        # ======================================================

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

        # ======================================================
        # LANDMARKS
        # ======================================================

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
        # MediaPipe Pose normally gives 33 landmarks.
        # ------------------------------------------------------

        try:

            if len(landmarks) < 29:

                return self._set_result(
                    self._waiting_result()
                )

        except TypeError:

            return self._set_result(
                self._waiting_result()
            )

        # ======================================================
        # REQUIRED LANDMARK VALIDATION
        # ======================================================

        required_indexes = (
            11,
            12,
            13,
            14,
            15,
            16,
            23,
            24,
            25,
            26,
            27,
            28,
        )

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

        # ======================================================
        # WORKOUT ENGINE
        # ======================================================

        try:

            result = (
                self.workout_engine.process_auto(
                    landmarks
                )
            )

        except RuntimeError as error:

            print(
                f"Workout engine error: {error}"
            )

            result = self._waiting_result()

        except Exception as error:

            print(
                f"Automatic detection error: {error}"
            )

            result = self._waiting_result()

        # ======================================================
        # NORMALIZE
        # ======================================================

        result = self._normalize_result(
            result
        )

        self.last_result = result

        # ======================================================
        # VOICE
        # ======================================================

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

        if not isinstance(
            result,
            dict,
        ):

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
                "candidates": {},
                "candidate_exercise": None,
                "candidate_frames": 0,
                "required_frames": 0,
            }

        # ------------------------------------------------------
        # Exercise.
        # ------------------------------------------------------

        exercise = result.get(
            "exercise"
        )

        detected_exercise = result.get(
            "detected_exercise"
        )

        # ------------------------------------------------------
        # Confidence.
        # ------------------------------------------------------

        try:

            confidence = float(
                result.get(
                    "confidence",
                    0.0,
                )
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
        # Reps.
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
        # Status.
        # ------------------------------------------------------

        status = str(
            result.get(
                "status",
                "active"
                if exercise
                else "waiting",
            )
        ).strip().lower()

        # ------------------------------------------------------
        # Candidates.
        # ------------------------------------------------------

        candidates = result.get(
            "candidates",
            {},
        )

        if not isinstance(
            candidates,
            dict,
        ):
            candidates = {}

        return {
            "exercise": exercise,
            "detected_exercise": (
                detected_exercise
                or exercise
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
            "candidates": candidates,
            "candidate_exercise": result.get(
                "candidate_exercise"
            ),
            "candidate_frames": result.get(
                "candidate_frames",
                0,
            ),
            "required_frames": result.get(
                "required_frames",
                0,
            ),
        }

    # ==========================================================
    # WAITING
    # ==========================================================

    def _waiting_result(self):

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
            "candidates": {},
            "candidate_exercise": None,
            "candidate_frames": 0,
            "required_frames": 0,
        }

    # ==========================================================
    # SET RESULT
    # ==========================================================

    def _set_result(self, result):

        result = self._normalize_result(
            result
        )

        self.last_result = result

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

        detected = result.get(
            "detected_exercise"
        )

        candidate = result.get(
            "candidate_exercise"
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

        candidates = result.get(
            "candidates",
            {},
        )

        # ------------------------------------------------------
        # Main exercise text.
        # ------------------------------------------------------

        if exercise:

            exercise_text = (
                str(exercise)
                .replace(
                    "_",
                    " ",
                )
                .title()
            )

        elif candidate:

            exercise_text = (
                "Detecting "
                + str(candidate)
                .replace(
                    "_",
                    " ",
                )
                .title()
            )

        elif detected:

            exercise_text = (
                "Detecting "
                + str(detected)
                .replace(
                    "_",
                    " ",
                )
                .title()
            )

        else:

            exercise_text = "Waiting..."

        # ======================================================
        # MAIN UI
        # ======================================================

        cv2.putText(
            frame,
            f"Exercise: {exercise_text}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Reps: {reps}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.2f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Status: {status}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

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

        if form:

            form_text = str(
                form
            )[:65]

            cv2.putText(
                frame,
                f"Form: {form_text}",
                (20, 215),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

        # ======================================================
        # DETECTION SCORES
        # ======================================================

        score_y = 260

        score_names = (
            (
                "squat",
                "Squat",
            ),
            (
                "lunge",
                "Lunge",
            ),
            (
                "bicep_curl",
                "Bicep Curl",
            ),
        )

        for key, label in score_names:

            value = candidates.get(
                key,
                0.0,
            )

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                value = 0.0

            cv2.putText(
                frame,
                f"{label}: {value:.2f}",
                (20, score_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

            score_y += 30

        # ======================================================
        # DETECTION CONFIRMATION
        # ======================================================

        candidate_frames = result.get(
            "candidate_frames",
            0,
        )

        required_frames = result.get(
            "required_frames",
            0,
        )

        if (
            candidate
            and required_frames > 0
        ):

            cv2.putText(
                frame,
                (
                    f"Confirming: "
                    f"{candidate_frames}/"
                    f"{required_frames}"
                ),
                (20, score_y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.workout_engine.reset()

        if (
            self.voice_controller
            is not None
        ):

            self.voice_controller.reset()

            self.voice_controller.announce_workout_reset()

        if (
            self.speech_worker
            is not None
        ):

            self.speech_worker.clear_queue()

        self.last_result = (
            self._waiting_result()
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        was_running = self.running

        self.running = False

        # ------------------------------------------------------
        # Voice stop.
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
        # Camera.
        # ------------------------------------------------------

        if self.camera is not None:

            self.camera.release()
            self.camera = None

        # ------------------------------------------------------
        # Workout.
        # ------------------------------------------------------

        if self.workout_engine is not None:

            self.workout_engine.stop()

        # ------------------------------------------------------
        # Speech.
        # ------------------------------------------------------

        if self.speech_worker is not None:

            try:
                self.speech_worker.stop()
            except Exception:
                pass

        cv2.destroyAllWindows()

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
            "Exercises            : "
            "SQUAT / LUNGE / BICEP CURL"
        )
        print(
            "Voice                : "
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

                # Mirror camera.
                frame = cv2.flip(
                    frame,
                    1,
                )

                # AI.
                result = self.process_frame(
                    frame
                )

                # UI.
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