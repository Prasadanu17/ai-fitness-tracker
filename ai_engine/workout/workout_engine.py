"""
Workout Engine
==============

Central orchestration layer for the AI Fitness Tracker.

Supports:

    Manual mode
        WorkoutEngine.start("squat")

    Automatic mode
        WorkoutEngine.start_auto()
        WorkoutEngine.process_auto(landmarks)

Automatic pipeline:

    landmarks
        ↓
    ExerciseDetector
        ↓
    stable exercise
        ↓
    ExerciseSelector
        ↓
    Exercise Analyzer
        ↓
    standardized result
"""


from ai_engine.detection.exercise_detector import ExerciseDetector
from ai_engine.registry.exercise_selector import ExerciseSelector


class WorkoutEngine:

    def __init__(self):

        self.selector = ExerciseSelector()
        self.detector = ExerciseDetector()

        self.is_active = False
        self.session_id = None

        self.auto_detect = False

        self.detected_exercise = None

        self.last_detection = {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
            "status": "waiting",
            "candidates": {},
        }

    # ==========================================================
    # MANUAL START
    # ==========================================================

    def start(
        self,
        exercise_name,
        **kwargs,
    ):

        analyzer = self.selector.select(
            exercise_name,
            **kwargs,
        )

        self.is_active = True
        self.auto_detect = False
        self.detected_exercise = None

        return analyzer

    # ==========================================================
    # AUTOMATIC START
    # ==========================================================

    def start_auto(self):

        self.selector.clear()
        self.detector.reset()

        self.is_active = True
        self.auto_detect = True

        self.detected_exercise = None

        self.last_detection = {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
            "status": "waiting",
            "candidates": {},
        }

        return True

    # ==========================================================
    # MANUAL PROCESS
    # ==========================================================

    def process(self, landmarks):

        if not self.is_active:
            raise RuntimeError(
                "No active workout. "
                "Call start() before process()."
            )

        if self.auto_detect:
            raise RuntimeError(
                "Workout is running in automatic mode. "
                "Call process_auto() instead."
            )

        analyzer = (
            self.selector.get_current_analyzer()
        )

        if analyzer is None:
            raise RuntimeError(
                "Workout is active but no analyzer "
                "is selected."
            )

        return analyzer.analyze(
            landmarks
        )

    # ==========================================================
    # AUTOMATIC PROCESS
    # ==========================================================

    def process_auto(self, landmarks):

        if not self.is_active:
            raise RuntimeError(
                "No active workout. "
                "Call start_auto() before process_auto()."
            )

        if not self.auto_detect:
            raise RuntimeError(
                "Workout is not running in automatic mode."
            )

        # ------------------------------------------------------
        # Detect.
        # ------------------------------------------------------

        detection = self.detector.detect(
            landmarks
        )

        self.last_detection = dict(
            detection
        )

        stable_exercise = detection.get(
            "exercise"
        )

        detected_exercise = detection.get(
            "detected_exercise"
        )

        confidence = detection.get(
            "confidence",
            0.0,
        )

        side = detection.get(
            "side"
        )

        status = detection.get(
            "status",
            "waiting_for_exercise",
        )

        candidates = detection.get(
            "candidates",
            {},
        )

        # ------------------------------------------------------
        # Nothing stable yet.
        #
        # IMPORTANT:
        # We do not create an analyzer until the detector
        # confirms the exercise.
        # ------------------------------------------------------

        if stable_exercise is None:

            return {
                "exercise": None,
                "detected_exercise": detected_exercise,
                "confidence": confidence,
                "side": side,
                "status": status,
                "reps": 0,
                "state": None,
                "form": None,
                "detection_mode": "automatic",
                "candidates": candidates,
                "candidate_exercise": detection.get(
                    "candidate_exercise"
                ),
                "candidate_frames": detection.get(
                    "candidate_frames",
                    0,
                ),
                "required_frames": detection.get(
                    "required_frames",
                    0,
                ),
            }

        # ------------------------------------------------------
        # Exercise changed.
        #
        # This happens only after ExerciseDetector has
        # confirmed the new exercise.
        # ------------------------------------------------------

        if (
            stable_exercise
            != self.detected_exercise
        ):

            self.selector.select(
                stable_exercise,
                side=side,
            )

            self.detected_exercise = (
                stable_exercise
            )

        # ------------------------------------------------------
        # Analyzer.
        # ------------------------------------------------------

        analyzer = (
            self.selector.get_current_analyzer()
        )

        if analyzer is None:
            raise RuntimeError(
                "Exercise was detected but analyzer "
                "could not be created."
            )

        # ------------------------------------------------------
        # Analyze.
        # ------------------------------------------------------

        result = analyzer.analyze(
            landmarks
        )

        if not isinstance(result, dict):
            result = {}

        # ------------------------------------------------------
        # Normalize/enrich analyzer result.
        # ------------------------------------------------------

        result["exercise"] = (
            result.get(
                "exercise",
                stable_exercise,
            )
            or stable_exercise
        )

        result["detected_exercise"] = (
            stable_exercise
        )

        result["confidence"] = (
            float(confidence)
        )

        result["side"] = (
            result.get("side")
            or side
        )

        result["status"] = (
            result.get(
                "status",
                "active",
            )
            or "active"
        )

        result["detection_mode"] = (
            "automatic"
        )

        result["candidates"] = (
            candidates
        )

        result["candidate_exercise"] = (
            detection.get(
                "candidate_exercise"
            )
        )

        result["candidate_frames"] = (
            detection.get(
                "candidate_frames",
                0,
            )
        )

        result["required_frames"] = (
            detection.get(
                "required_frames",
                0,
            )
        )

        return result

    # ==========================================================
    # CURRENT RESULT
    # ==========================================================

    def get_result(self):

        if not self.is_active:
            return None

        analyzer = (
            self.selector.get_current_analyzer()
        )

        if analyzer is None:
            return None

        result = analyzer.get_result()

        if not isinstance(result, dict):
            result = {}

        if self.auto_detect:

            result["exercise"] = (
                result.get(
                    "exercise"
                )
                or self.detected_exercise
            )

            result["confidence"] = (
                self.detector.get_confidence()
            )

            result["detection_mode"] = (
                "automatic"
            )

            result["candidates"] = (
                self.detector.get_scores()
            )

        return result

    # ==========================================================
    # CURRENT EXERCISE
    # ==========================================================

    def get_current_exercise(self):

        return self.selector.get_current_exercise()

    # ==========================================================
    # DETECTED EXERCISE
    # ==========================================================

    def get_detected_exercise(self):

        return self.detected_exercise

    # ==========================================================
    # DETECTION CONFIDENCE
    # ==========================================================

    def get_detection_confidence(self):

        return self.detector.get_confidence()

    # ==========================================================
    # DETECTION SCORES
    # ==========================================================

    def get_detection_scores(self):

        return self.detector.get_scores()

    # ==========================================================
    # DETECTION STATUS
    # ==========================================================

    def get_detection_status(self):

        return self.detector.get_status()

    # ==========================================================
    # CURRENT ANALYZER
    # ==========================================================

    def get_current_analyzer(self):

        return (
            self.selector.get_current_analyzer()
        )

    # ==========================================================
    # AVAILABLE EXERCISES
    # ==========================================================

    def get_available_exercises(self):

        return (
            self.selector.get_available_exercises()
        )

    # ==========================================================
    # WORKOUT MODE
    # ==========================================================

    def is_auto_mode(self):

        return self.auto_detect

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        self.selector.clear()
        self.detector.reset()

        self.is_active = False
        self.auto_detect = False

        self.detected_exercise = None
        self.session_id = None

        self.last_detection = {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
            "status": "waiting",
            "candidates": {},
        }

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        if not self.is_active:
            return

        # ------------------------------------------------------
        # Automatic mode:
        #
        # Completely reset detection so the next exercise can
        # be detected from scratch.
        # ------------------------------------------------------

        if self.auto_detect:

            self.selector.clear()
            self.detector.reset()

            self.detected_exercise = None

            self.last_detection = {
                "exercise": None,
                "confidence": 0.0,
                "side": None,
                "status": "waiting",
                "candidates": {},
            }

            return

        # ------------------------------------------------------
        # Manual mode:
        #
        # Keep selected exercise but reset analyzer.
        # ------------------------------------------------------

        analyzer = (
            self.selector.get_current_analyzer()
        )

        if analyzer is not None:
            reset_method = getattr(
                analyzer,
                "reset",
                None,
            )

            if callable(reset_method):
                reset_method()

    # ==========================================================
    # STATUS
    # ==========================================================

    def is_running(self):

        return self.is_active