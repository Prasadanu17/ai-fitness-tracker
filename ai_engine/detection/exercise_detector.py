"""
Exercise Detector

Detects:
    - Squat
    - Bicep Curl
    - Lunge

Design goals:
    - Strong bilateral leg evidence -> squat
    - Strong front/back leg evidence -> lunge
    - Strong elbow bend -> bicep curl
    - Bent knees do NOT automatically reject bicep curls
    - Seated bicep curls remain valid
    - Temporal stabilization prevents noisy switching

Important:
    Knee-angle difference alone is NOT sufficient to classify a lunge.
    Camera perspective can make a normal squat appear asymmetric.
"""

from collections import deque

from ai_engine.analysis.angle_calculator import AngleCalculator


class ExerciseDetector:

    # ==========================================================
    # MEDIAPIPE LANDMARK INDEXES
    # ==========================================================

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16

    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    REQUIRED_LANDMARK_COUNT = 33

    # ==========================================================
    # VISIBILITY
    # ==========================================================

    MIN_VISIBILITY = 0.35

    # ==========================================================
    # BICEP CURL
    # ==========================================================

    BICEP_CURL_THRESHOLD = 105
    BICEP_SIDE_ADVANTAGE = 20
    BICEP_MIN_CONFIDENCE = 0.62

    # ==========================================================
    # SQUAT
    # ==========================================================

    LEG_BENT_THRESHOLD = 130
    DEEP_SQUAT_THRESHOLD = 105

    # A squat should tolerate reasonable left/right differences.
    SQUAT_MAX_ANGLE_DIFFERENCE = 45

    # ==========================================================
    # LUNGE
    # ==========================================================

    # A lunge needs substantially different leg states.
    LUNGE_MIN_ANGLE_DIFFERENCE = 45

    # Strong evidence:
    # one leg clearly bent while the other is relatively extended.
    LUNGE_BENT_THRESHOLD = 115
    LUNGE_EXTENDED_THRESHOLD = 150

    # Very deep unilateral bend can still provide lunge evidence,
    # but it should not override a clearly bilateral squat.
    LUNGE_DEEP_BEND_THRESHOLD = 105

    # ==========================================================
    # TEMPORAL STABILIZATION
    # ==========================================================

    CONFIRMATION_FRAMES = 5
    HISTORY_SIZE = 8
    STABLE_MATCHES_REQUIRED = 3

    # ==========================================================
    # INIT
    # ==========================================================

    def __init__(
        self,
        confirmation_frames=None,
        minimum_confidence=0.60,
    ):
        self.confirmation_frames = (
            confirmation_frames
            if confirmation_frames is not None
            else self.CONFIRMATION_FRAMES
        )

        self.minimum_confidence = float(
            minimum_confidence
        )

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        self.pending_exercise = None
        self.pending_side = None
        self.pending_count = 0
        self.stable_match_count = 0

        self.detection_history = deque(
            maxlen=self.HISTORY_SIZE
        )

        self._last_landmarks = None
        self._last_arm_angles = None
        self._last_leg_angles = None

        self._last_candidates = {
            "squat": 0.0,
            "bicep_curl": 0.0,
            "lunge": 0.0,
        }

    # ==========================================================
    # LANDMARK VALIDATION
    # ==========================================================

    @classmethod
    def _is_valid_landmark(cls, landmark):
        if landmark is None:
            return False

        try:
            x = float(landmark.x)
            y = float(landmark.y)
            z = float(landmark.z)

            visibility = float(
                getattr(
                    landmark,
                    "visibility",
                    1.0,
                )
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return False

        if not (
            x == x
            and y == y
            and z == z
        ):
            return False

        if visibility < cls.MIN_VISIBILITY:
            return False

        return True

    @staticmethod
    def _distance(point_a, point_b):
        dx = float(point_a.x) - float(point_b.x)
        dy = float(point_a.y) - float(point_b.y)
        dz = float(point_a.z) - float(point_b.z)

        return (
            dx * dx
            + dy * dy
            + dz * dz
        ) ** 0.5

    @staticmethod
    def _horizontal_distance(point_a, point_b):
        return abs(
            float(point_a.x)
            - float(point_b.x)
        )

    def _has_valid_landmarks(
        self,
        landmarks,
        indexes,
    ):
        if landmarks is None:
            return False

        try:
            if len(landmarks) <= max(indexes):
                return False
        except (
            TypeError,
            ValueError,
        ):
            return False

        for index in indexes:
            if not self._is_valid_landmark(
                landmarks[index]
            ):
                return False

        return True

    def _has_valid_pose(self, landmarks):
        if landmarks is None:
            return False

        try:
            if len(landmarks) < self.REQUIRED_LANDMARK_COUNT:
                return False
        except (
            TypeError,
            ValueError,
        ):
            return False

        required_indexes = (
            self.LEFT_SHOULDER,
            self.RIGHT_SHOULDER,
            self.LEFT_ELBOW,
            self.RIGHT_ELBOW,
            self.LEFT_WRIST,
            self.RIGHT_WRIST,
            self.LEFT_HIP,
            self.RIGHT_HIP,
            self.LEFT_KNEE,
            self.RIGHT_KNEE,
            self.LEFT_ANKLE,
            self.RIGHT_ANKLE,
        )

        if not self._has_valid_landmarks(
            landmarks,
            required_indexes,
        ):
            return False

        body_pairs = (
            (
                self.RIGHT_SHOULDER,
                self.RIGHT_ELBOW,
            ),
            (
                self.RIGHT_ELBOW,
                self.RIGHT_WRIST,
            ),
            (
                self.RIGHT_HIP,
                self.RIGHT_KNEE,
            ),
            (
                self.RIGHT_KNEE,
                self.RIGHT_ANKLE,
            ),
            (
                self.LEFT_SHOULDER,
                self.LEFT_ELBOW,
            ),
            (
                self.LEFT_ELBOW,
                self.LEFT_WRIST,
            ),
            (
                self.LEFT_HIP,
                self.LEFT_KNEE,
            ),
            (
                self.LEFT_KNEE,
                self.LEFT_ANKLE,
            ),
        )

        for index_a, index_b in body_pairs:
            if self._distance(
                landmarks[index_a],
                landmarks[index_b],
            ) < 0.001:
                return False

        return True

    # ==========================================================
    # ANGLE
    # ==========================================================

    @staticmethod
    def _calculate_angle(
        point_a,
        point_b,
        point_c,
    ):
        return AngleCalculator.calculate_angle(
            point_a,
            point_b,
            point_c,
        )

    # ==========================================================
    # ARM ANGLES
    # ==========================================================

    def _get_arm_angles(self, landmarks):
        candidates = []

        right_indexes = (
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):
            angle = self._calculate_angle(
                landmarks[self.RIGHT_SHOULDER],
                landmarks[self.RIGHT_ELBOW],
                landmarks[self.RIGHT_WRIST],
            )

            candidates.append(
                ("right", angle)
            )

        left_indexes = (
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):
            angle = self._calculate_angle(
                landmarks[self.LEFT_SHOULDER],
                landmarks[self.LEFT_ELBOW],
                landmarks[self.LEFT_WRIST],
            )

            candidates.append(
                ("left", angle)
            )

        return candidates

    # ==========================================================
    # LEG ANGLES
    # ==========================================================

    def _get_leg_angles(self, landmarks):
        right_angle = None
        left_angle = None

        right_indexes = (
            self.RIGHT_HIP,
            self.RIGHT_KNEE,
            self.RIGHT_ANKLE,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):
            right_angle = self._calculate_angle(
                landmarks[self.RIGHT_HIP],
                landmarks[self.RIGHT_KNEE],
                landmarks[self.RIGHT_ANKLE],
            )

        left_indexes = (
            self.LEFT_HIP,
            self.LEFT_KNEE,
            self.LEFT_ANKLE,
        )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):
            left_angle = self._calculate_angle(
                landmarks[self.LEFT_HIP],
                landmarks[self.LEFT_KNEE],
                landmarks[self.LEFT_ANKLE],
            )

        return right_angle, left_angle

    # ==========================================================
    # SEATED POSTURE
    # ==========================================================

    def _is_seated_posture(self, landmarks):
        """
        Informational seated-pose helper.

        IMPORTANT:
        This method never suppresses bicep curls.

        Seated bicep curls are valid.
        """

        required = (
            self.LEFT_HIP,
            self.RIGHT_HIP,
            self.LEFT_KNEE,
            self.RIGHT_KNEE,
            self.LEFT_ANKLE,
            self.RIGHT_ANKLE,
        )

        if not self._has_valid_landmarks(
            landmarks,
            required,
        ):
            return False

        offsets = []
        scales = []

        pairs = (
            (
                self.LEFT_HIP,
                self.LEFT_KNEE,
                self.LEFT_ANKLE,
            ),
            (
                self.RIGHT_HIP,
                self.RIGHT_KNEE,
                self.RIGHT_ANKLE,
            ),
        )

        for (
            hip_idx,
            knee_idx,
            ankle_idx,
        ) in pairs:

            hip = landmarks[hip_idx]
            knee = landmarks[knee_idx]
            ankle = landmarks[ankle_idx]

            hip_knee_distance = self._distance(
                hip,
                knee,
            )

            if hip_knee_distance <= 0.001:
                continue

            offsets.append(
                self._horizontal_distance(
                    knee,
                    ankle,
                )
            )

            scales.append(
                hip_knee_distance
            )

        if not offsets:
            return False

        average_offset = (
            sum(offsets)
            / len(offsets)
        )

        average_scale = (
            sum(scales)
            / len(scales)
        )

        if average_scale <= 0.001:
            return False

        ratio = (
            average_offset
            / average_scale
        )

        threshold = getattr(
            self,
            "SEATED_ANKLE_OFFSET_RATIO",
            0.85,
        )

        return ratio >= threshold

    # ==========================================================
    # BICEP CURL
    # ==========================================================

    def _detect_bicep_curl(self, landmarks):
        candidates = self._get_arm_angles(
            landmarks
        )

        if not candidates:
            return None, 0.0, None

        candidates.sort(
            key=lambda item: item[1]
        )

        side, angle = candidates[0]

        if angle > self.BICEP_CURL_THRESHOLD:
            return None, 0.0, None

        if angle <= 80:
            confidence = 0.90
        elif angle <= 90:
            confidence = 0.86
        elif angle <= 100:
            confidence = 0.80
        elif angle <= 105:
            confidence = 0.70
        else:
            confidence = 0.62

        if len(candidates) >= 2:
            second_angle = candidates[1][1]

            advantage = (
                second_angle - angle
            )

            if advantage >= self.BICEP_SIDE_ADVANTAGE:
                confidence += 0.05

        confidence = min(
            0.96,
            confidence,
        )

        if confidence < self.BICEP_MIN_CONFIDENCE:
            return None, 0.0, None

        # NEVER inspect knees here.
        #
        # Seated bicep curls are intentionally supported.

        return (
            "bicep_curl",
            round(confidence, 2),
            side,
        )

    # ==========================================================
    # SQUAT EVIDENCE
    # ==========================================================

    def _get_squat_evidence(
        self,
        right_angle,
        left_angle,
    ):
        if (
            right_angle is None
            or left_angle is None
        ):
            return 0.0, None

        difference = abs(
            right_angle - left_angle
        )

        right_bent = (
            right_angle
            <= self.LEG_BENT_THRESHOLD
        )

        left_bent = (
            left_angle
            <= self.LEG_BENT_THRESHOLD
        )

        # Both knees need meaningful flexion.
        if not (
            right_bent
            and left_bent
        ):
            return 0.0, None

        # Normal squat asymmetry is allowed.
        if difference > self.SQUAT_MAX_ANGLE_DIFFERENCE:
            return 0.0, None

        average_angle = (
            right_angle + left_angle
        ) / 2.0

        if (
            right_angle <= self.DEEP_SQUAT_THRESHOLD
            and left_angle <= self.DEEP_SQUAT_THRESHOLD
        ):
            confidence = 0.94

        elif average_angle <= 115:
            confidence = 0.90

        elif average_angle <= 125:
            confidence = 0.86

        else:
            confidence = 0.82

        # Slightly reduce confidence for asymmetry,
        # but do not immediately classify it as a lunge.
        if difference > 30:
            confidence -= 0.05
        elif difference > 20:
            confidence -= 0.02

        confidence = max(
            0.0,
            min(0.96, confidence),
        )

        side = (
            "right"
            if right_angle <= left_angle
            else "left"
        )

        return confidence, side

    # ==========================================================
    # LUNGE EVIDENCE
    # ==========================================================

    def _get_lunge_evidence(
        self,
        right_angle,
        left_angle,
    ):
        if (
            right_angle is None
            or left_angle is None
        ):
            return 0.0, None

        difference = abs(
            right_angle - left_angle
        )

        # Angle difference alone is NOT enough.
        if difference < self.LUNGE_MIN_ANGLE_DIFFERENCE:
            return 0.0, None

        # ------------------------------------------------------
        # RIGHT LEG FORWARD / BENT
        # ------------------------------------------------------

        right_bent = (
            right_angle
            <= self.LUNGE_BENT_THRESHOLD
        )

        left_extended = (
            left_angle
            >= self.LUNGE_EXTENDED_THRESHOLD
        )

        if right_bent and left_extended:
            confidence = 0.86

            if right_angle <= self.LUNGE_DEEP_BEND_THRESHOLD:
                confidence = 0.92

            if difference >= 70:
                confidence = min(
                    0.96,
                    confidence + 0.03,
                )

            return (
                confidence,
                "right",
            )

        # ------------------------------------------------------
        # LEFT LEG FORWARD / BENT
        # ------------------------------------------------------

        left_bent = (
            left_angle
            <= self.LUNGE_BENT_THRESHOLD
        )

        right_extended = (
            right_angle
            >= self.LUNGE_EXTENDED_THRESHOLD
        )

        if left_bent and right_extended:
            confidence = 0.86

            if left_angle <= self.LUNGE_DEEP_BEND_THRESHOLD:
                confidence = 0.92

            if difference >= 70:
                confidence = min(
                    0.96,
                    confidence + 0.03,
                )

            return (
                confidence,
                "left",
            )

        # ------------------------------------------------------
        # Do NOT guess a lunge when both legs are moderately bent.
        # ------------------------------------------------------

        return 0.0, None

    # ==========================================================
    # LEG EXERCISE
    # ==========================================================

    def _detect_leg_exercise(self, landmarks):
        right_angle, left_angle = (
            self._get_leg_angles(
                landmarks
            )
        )

        if (
            right_angle is None
            and left_angle is None
        ):
            return None, 0.0, None

        # ------------------------------------------------------
        # BOTH LEGS AVAILABLE
        # ------------------------------------------------------

        if (
            right_angle is not None
            and left_angle is not None
        ):
            squat_confidence, squat_side = (
                self._get_squat_evidence(
                    right_angle,
                    left_angle,
                )
            )

            lunge_confidence, lunge_side = (
                self._get_lunge_evidence(
                    right_angle,
                    left_angle,
                )
            )

            # --------------------------------------------------
            # IMPORTANT PRIORITY
            #
            # Strong bilateral squat evidence beats weak
            # asymmetry.
            # --------------------------------------------------

            if squat_confidence >= 0.80:
                # Only allow lunge to win when there is
                # unmistakable front/back asymmetry.
                if (
                    lunge_confidence >= 0.92
                    and lunge_confidence
                    > squat_confidence + 0.06
                ):
                    return (
                        "lunge",
                        lunge_confidence,
                        lunge_side,
                    )

                return (
                    "squat",
                    squat_confidence,
                    squat_side,
                )

            if lunge_confidence >= 0.80:
                return (
                    "lunge",
                    lunge_confidence,
                    lunge_side,
                )

            return None, 0.0, None

        # ------------------------------------------------------
        # ONE LEG AVAILABLE
        # ------------------------------------------------------

        if right_angle is not None:
            if right_angle <= self.LUNGE_DEEP_BEND_THRESHOLD:
                return (
                    "lunge",
                    0.72,
                    "right",
                )

        if left_angle is not None:
            if left_angle <= self.LUNGE_DEEP_BEND_THRESHOLD:
                return (
                    "lunge",
                    0.72,
                    "left",
                )

        return None, 0.0, None

    # ==========================================================
    # CANDIDATE ANALYSIS
    # ==========================================================

    def _calculate_candidates(self, landmarks):
        candidates = {
            "squat": 0.0,
            "bicep_curl": 0.0,
            "lunge": 0.0,
        }

        curl, curl_confidence, _ = (
            self._detect_bicep_curl(
                landmarks
            )
        )

        if curl is not None:
            candidates["bicep_curl"] = (
                curl_confidence
            )

        right_angle, left_angle = (
            self._get_leg_angles(
                landmarks
            )
        )

        squat_confidence, _ = (
            self._get_squat_evidence(
                right_angle,
                left_angle,
            )
        )

        lunge_confidence, _ = (
            self._get_lunge_evidence(
                right_angle,
                left_angle,
            )
        )

        candidates["squat"] = round(
            squat_confidence,
            2,
        )

        candidates["lunge"] = round(
            lunge_confidence,
            2,
        )

        return candidates

    def get_candidates(self):
        return dict(
            self._last_candidates
        )

    # ==========================================================
    # RAW DETECTION
    # ==========================================================

    def _detect_raw(self, landmarks):
        self._last_landmarks = landmarks

        self._last_arm_angles = (
            self._get_arm_angles(
                landmarks
            )
        )

        self._last_leg_angles = (
            self._get_leg_angles(
                landmarks
            )
        )

        self._last_candidates = (
            self._calculate_candidates(
                landmarks
            )
        )

        curl, curl_confidence, curl_side = (
            self._detect_bicep_curl(
                landmarks
            )
        )

        leg, leg_confidence, leg_side = (
            self._detect_leg_exercise(
                landmarks
            )
        )

        # ------------------------------------------------------
        # STRONG SQUAT
        # ------------------------------------------------------

        if leg == "squat":
            return (
                "squat",
                leg_confidence,
                leg_side,
            )

        # ------------------------------------------------------
        # STRONG LUNGE
        # ------------------------------------------------------

        if leg == "lunge":
            return (
                "lunge",
                leg_confidence,
                leg_side,
            )

        # ------------------------------------------------------
        # BICEP CURL
        #
        # Bent knees are completely allowed.
        # ------------------------------------------------------

        if curl is not None:
            return (
                curl,
                curl_confidence,
                curl_side,
            )

        return None, 0.0, None

    # ==========================================================
    # TEMPORAL STABILIZATION
    # ==========================================================

    def _stabilize(
        self,
        exercise,
        confidence,
        side,
    ):
        # ------------------------------------------------------
        # No current exercise
        # ------------------------------------------------------

        if self.current_exercise is None:

            if exercise is None:
                self.pending_exercise = None
                self.pending_side = None
                self.pending_count = 0

                return self._empty_result()

            if exercise == self.pending_exercise:
                self.pending_count += 1
            else:
                self.pending_exercise = exercise
                self.pending_side = side
                self.pending_count = 1

            if (
                self.pending_count
                >= self.confirmation_frames
            ):
                self.current_exercise = exercise
                self.current_confidence = confidence
                self.current_side = side

                self.pending_exercise = None
                self.pending_side = None
                self.pending_count = 0

                return self._set_result(
                    exercise,
                    confidence,
                    side,
                )

            return self._empty_result()

        # ------------------------------------------------------
        # Same exercise
        # ------------------------------------------------------

        if exercise == self.current_exercise:
            self.stable_match_count += 1

            self.current_confidence = (
                0.80
                * self.current_confidence
                + 0.20
                * confidence
            )

            if side is not None:
                self.current_side = side

            self.pending_exercise = None
            self.pending_side = None
            self.pending_count = 0

            return self._set_result(
                self.current_exercise,
                self.current_confidence,
                self.current_side,
            )

        # ------------------------------------------------------
        # No candidate during transition
        # ------------------------------------------------------

        if exercise is None:
            self.stable_match_count = 0

            return self._set_result(
                self.current_exercise,
                self.current_confidence,
                self.current_side,
            )

        # ------------------------------------------------------
        # Different exercise
        # ------------------------------------------------------

        if exercise == self.pending_exercise:
            self.pending_count += 1
        else:
            self.pending_exercise = exercise
            self.pending_side = side
            self.pending_count = 1

        # ------------------------------------------------------
        # Require consecutive frames before switching
        # ------------------------------------------------------

        if (
            self.pending_count
            >= self.confirmation_frames
        ):
            self.current_exercise = exercise
            self.current_confidence = confidence
            self.current_side = side

            self.pending_exercise = None
            self.pending_side = None
            self.pending_count = 0
            self.stable_match_count = 0

            return self._set_result(
                exercise,
                confidence,
                side,
            )

        # Keep current exercise during transition.
        return self._set_result(
            self.current_exercise,
            self.current_confidence,
            self.current_side,
        )

    # ==========================================================
    # MAIN DETECTION
    # ==========================================================

    def detect(self, landmarks):

        if landmarks is None:
            return self._stabilize(
                None,
                0.0,
                None,
            )

        try:
            if len(landmarks) < self.REQUIRED_LANDMARK_COUNT:
                return self._stabilize(
                    None,
                    0.0,
                    None,
                )
        except (
            TypeError,
            ValueError,
        ):
            return self._empty_result()

        if not self._has_valid_pose(
            landmarks
        ):
            return self._stabilize(
                None,
                0.0,
                None,
            )

        exercise, confidence, side = (
            self._detect_raw(
                landmarks
            )
        )

        if (
            exercise is not None
            and confidence < self.minimum_confidence
        ):
            exercise = None
            confidence = 0.0
            side = None

        self.detection_history.append(
            exercise
        )

        return self._stabilize(
            exercise,
            confidence,
            side,
        )

    # ==========================================================
    # RESULT HELPERS
    # ==========================================================

    def _set_result(
        self,
        exercise,
        confidence,
        side,
    ):
        self.current_exercise = exercise
        self.current_confidence = float(
            confidence
        )
        self.current_side = side

        return {
            "exercise": exercise,
            "confidence": round(
                float(confidence),
                2,
            ),
            "side": side,
        }

    def _empty_result(self):
        return {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
        }

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):
        return self.current_exercise

    def get_confidence(self):
        return self.current_confidence

    def get_current_side(self):
        return self.current_side

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        self.detection_history.clear()

        self.pending_exercise = None
        self.pending_side = None
        self.pending_count = 0
        self.stable_match_count = 0

        self._last_landmarks = None
        self._last_arm_angles = None
        self._last_leg_angles = None

        self._last_candidates = {
            "squat": 0.0,
            "bicep_curl": 0.0,
            "lunge": 0.0,
        }