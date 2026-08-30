"""
Exercise Detector
=================

Stable automatic exercise detection for the AI Fitness Tracker.

Supported exercises:
    - squat
    - bicep_curl
    - lunge

Detection strategy:
    MediaPipe landmarks
        |
        +--> body geometry
        |
        +--> exercise-specific scores
        |
        +--> temporal confirmation
        |
        +--> stable exercise

Important:
    The detector does NOT switch exercises from a single frame.

    This prevents:
        squat -> bicep curl -> squat

    caused by temporary landmark noise or naturally bent arms.
"""


from ai_engine.analysis.angle_calculator import AngleCalculator


class ExerciseDetector:
    """
    Stateful exercise detector.

    The detector evaluates all supported exercises and chooses
    the strongest candidate only after it remains consistent
    for several frames.
    """

    # ==========================================================
    # MEDIAPIPE LANDMARKS
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

    REQUIRED_LANDMARK_COUNT = 29

    # ==========================================================
    # VALIDATION
    # ==========================================================

    MIN_VISIBILITY = 0.30

    # ==========================================================
    # DETECTION SETTINGS
    # ==========================================================

    # Minimum score required to consider an exercise.
    MIN_DETECTION_SCORE = 0.58

    # Minimum confidence returned for a stable detection.
    MIN_STABLE_CONFIDENCE = 0.70

    # Number of consecutive frames required before changing
    # the stable exercise.
    CONFIRMATION_FRAMES = 6

    # Number of frames to tolerate temporary loss of detection.
    LOST_FRAME_TOLERANCE = 12

    # Existing exercise gets a slight stability advantage.
    STABILITY_BONUS = 0.05

    # ==========================================================
    # SQUAT
    # ==========================================================

    SQUAT_KNEE_START = 175
    SQUAT_KNEE_BENT = 145
    SQUAT_KNEE_DEEP = 105

    SQUAT_MAX_ASYMMETRY = 32

    # ==========================================================
    # LUNGE
    # ==========================================================

    LUNGE_BENT_KNEE = 145
    LUNGE_DEEP_KNEE = 105

    LUNGE_MIN_ASYMMETRY = 25
    LUNGE_STRONG_ASYMMETRY = 45

    # ==========================================================
    # BICEP CURL
    # ==========================================================

    CURL_ELBOW_START = 165
    CURL_ELBOW_BENT = 125
    CURL_ELBOW_DEEP = 80

    # Wrist should move toward shoulder for a curl.
    CURL_WRIST_SHOULDER_RATIO = 0.95

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        confirmation_frames=CONFIRMATION_FRAMES,
    ):
        self.confirmation_frames = max(
            1,
            int(confirmation_frames),
        )

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        # Candidate waiting for confirmation.
        self.candidate_exercise = None
        self.candidate_side = None
        self.candidate_confidence = 0.0
        self.candidate_frames = 0

        # Number of consecutive frames without a reliable pose.
        self.lost_frames = 0

        # Last complete score set.
        self.current_scores = {
            "squat": 0.0,
            "bicep_curl": 0.0,
            "lunge": 0.0,
        }

        self.current_status = "waiting"

    # ==========================================================
    # LANDMARK VALIDATION
    # ==========================================================

    @staticmethod
    def _is_valid_landmark(landmark):
        """
        Check whether a MediaPipe landmark is usable.
        """

        if landmark is None:
            return False

        if not hasattr(landmark, "x"):
            return False

        if not hasattr(landmark, "y"):
            return False

        try:
            x = float(landmark.x)
            y = float(landmark.y)
        except (TypeError, ValueError):
            return False

        if not (-1.0 <= x <= 2.0):
            return False

        if not (-1.0 <= y <= 2.0):
            return False

        if hasattr(landmark, "visibility"):
            try:
                visibility = float(landmark.visibility)

                if visibility < ExerciseDetector.MIN_VISIBILITY:
                    return False

            except (TypeError, ValueError):
                return False

        return True

    @staticmethod
    def _distance(point_a, point_b):
        """
        Euclidean 2D distance.
        """

        dx = float(point_a.x) - float(point_b.x)
        dy = float(point_a.y) - float(point_b.y)

        return (dx * dx + dy * dy) ** 0.5

    def _has_valid_landmarks(
        self,
        landmarks,
        indexes,
    ):
        """
        Verify required landmarks.
        """

        if landmarks is None:
            return False

        try:
            if len(landmarks) <= max(indexes):
                return False
        except TypeError:
            return False

        for index in indexes:
            if not self._is_valid_landmark(
                landmarks[index]
            ):
                return False

        return True

    def _has_valid_pose(self, landmarks):
        """
        Validate the overall body pose.
        """

        if landmarks is None:
            return False

        try:
            if len(landmarks) < self.REQUIRED_LANDMARK_COUNT:
                return False
        except TypeError:
            return False

        required = (
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
            required,
        ):
            return False

        # Reject collapsed landmarks.
        body_segments = (
            (
                self.LEFT_SHOULDER,
                self.LEFT_ELBOW,
            ),
            (
                self.LEFT_ELBOW,
                self.LEFT_WRIST,
            ),
            (
                self.RIGHT_SHOULDER,
                self.RIGHT_ELBOW,
            ),
            (
                self.RIGHT_ELBOW,
                self.RIGHT_WRIST,
            ),
            (
                self.LEFT_HIP,
                self.LEFT_KNEE,
            ),
            (
                self.LEFT_KNEE,
                self.LEFT_ANKLE,
            ),
            (
                self.RIGHT_HIP,
                self.RIGHT_KNEE,
            ),
            (
                self.RIGHT_KNEE,
                self.RIGHT_ANKLE,
            ),
        )

        for index_a, index_b in body_segments:
            if self._distance(
                landmarks[index_a],
                landmarks[index_b],
            ) < 0.001:
                return False

        return True

    # ==========================================================
    # ANGLES
    # ==========================================================

    @staticmethod
    def _angle(
        point_a,
        point_b,
        point_c,
    ):
        return AngleCalculator.calculate_angle(
            point_a,
            point_b,
            point_c,
        )

    def _get_knee_angles(self, landmarks):
        """
        Return:

            right knee angle
            left knee angle
        """

        right = None
        left = None

        right_indexes = (
            self.RIGHT_HIP,
            self.RIGHT_KNEE,
            self.RIGHT_ANKLE,
        )

        left_indexes = (
            self.LEFT_HIP,
            self.LEFT_KNEE,
            self.LEFT_ANKLE,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):
            right = self._angle(
                landmarks[self.RIGHT_HIP],
                landmarks[self.RIGHT_KNEE],
                landmarks[self.RIGHT_ANKLE],
            )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):
            left = self._angle(
                landmarks[self.LEFT_HIP],
                landmarks[self.LEFT_KNEE],
                landmarks[self.LEFT_ANKLE],
            )

        return right, left

    def _get_elbow_angles(self, landmarks):
        """
        Return:

            right elbow angle
            left elbow angle
        """

        right = None
        left = None

        right_indexes = (
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
        )

        left_indexes = (
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):
            right = self._angle(
                landmarks[self.RIGHT_SHOULDER],
                landmarks[self.RIGHT_ELBOW],
                landmarks[self.RIGHT_WRIST],
            )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):
            left = self._angle(
                landmarks[self.LEFT_SHOULDER],
                landmarks[self.LEFT_ELBOW],
                landmarks[self.LEFT_WRIST],
            )

        return right, left

    # ==========================================================
    # NORMALIZE
    # ==========================================================

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(
            minimum,
            min(
                maximum,
                float(value),
            ),
        )

    @staticmethod
    def _range_score(
        value,
        start,
        target,
    ):
        """
        Convert an angle into a 0..1 bending score.

        start:
            mostly straight

        target:
            strongly bent
        """

        if value is None:
            return 0.0

        if value >= start:
            return 0.0

        if value <= target:
            return 1.0

        return ExerciseDetector._clamp(
            (start - value)
            / (start - target)
        )

    # ==========================================================
    # BICEP CURL SCORE
    # ==========================================================

    def _score_bicep_curl(self, landmarks):
        """
        Score both arms.

        A curl requires more than a bent elbow.

        We additionally check that the wrist is moving toward
        the shoulder region rather than simply having the arm
        bent during another exercise.
        """

        candidates = []

        arm_data = (
            (
                "right",
                self.RIGHT_SHOULDER,
                self.RIGHT_ELBOW,
                self.RIGHT_WRIST,
            ),
            (
                "left",
                self.LEFT_SHOULDER,
                self.LEFT_ELBOW,
                self.LEFT_WRIST,
            ),
        )

        for (
            side,
            shoulder_index,
            elbow_index,
            wrist_index,
        ) in arm_data:

            indexes = (
                shoulder_index,
                elbow_index,
                wrist_index,
            )

            if not self._has_valid_landmarks(
                landmarks,
                indexes,
            ):
                continue

            shoulder = landmarks[shoulder_index]
            elbow = landmarks[elbow_index]
            wrist = landmarks[wrist_index]

            elbow_angle = self._angle(
                shoulder,
                elbow,
                wrist,
            )

            bend_score = self._range_score(
                elbow_angle,
                self.CURL_ELBOW_START,
                self.CURL_ELBOW_DEEP,
            )

            shoulder_wrist = self._distance(
                shoulder,
                wrist,
            )

            shoulder_elbow = self._distance(
                shoulder,
                elbow,
            )

            elbow_wrist = self._distance(
                elbow,
                wrist,
            )

            # Avoid division problems.
            arm_length = max(
                shoulder_elbow + elbow_wrist,
                0.001,
            )

            # During a curl the wrist should be relatively close
            # to the shoulder compared with a fully extended arm.
            proximity_score = self._clamp(
                1.0
                - (
                    shoulder_wrist
                    / arm_length
                )
            )

            # Elbow must actually be bent.
            if elbow_angle > self.CURL_ELBOW_START:
                proximity_score *= 0.35

            score = (
                bend_score * 0.65
                + proximity_score * 0.35
            )

            candidates.append(
                (
                    side,
                    self._clamp(score),
                    elbow_angle,
                )
            )

        if not candidates:
            return 0.0, None

        side, score, _ = max(
            candidates,
            key=lambda item: item[1],
        )

        # A curl should have a meaningful arm signal.
        if score < self.MIN_DETECTION_SCORE:
            return 0.0, None

        return score, side

    # ==========================================================
    # SQUAT SCORE
    # ==========================================================

    def _score_squat(self, landmarks):
        """
        Score a squat.

        Squat characteristics:
            - both knees bend
            - knee angles are reasonably symmetrical
            - both legs participate
        """

        right, left = self._get_knee_angles(
            landmarks
        )

        if right is None or left is None:
            return 0.0, None

        difference = abs(
            right - left
        )

        if difference > self.SQUAT_MAX_ASYMMETRY:
            return 0.0, None

        right_bend = self._range_score(
            right,
            self.SQUAT_KNEE_START,
            self.SQUAT_KNEE_DEEP,
        )

        left_bend = self._range_score(
            left,
            self.SQUAT_KNEE_START,
            self.SQUAT_KNEE_DEEP,
        )

        bend_score = (
            right_bend + left_bend
        ) / 2.0

        symmetry_score = self._clamp(
            1.0
            - (
                difference
                / self.SQUAT_MAX_ASYMMETRY
            )
        )

        score = (
            bend_score * 0.72
            + symmetry_score * 0.28
        )

        if (
            right > self.SQUAT_KNEE_BENT
            and left > self.SQUAT_KNEE_BENT
        ):
            score *= 0.55

        if score < self.MIN_DETECTION_SCORE:
            return 0.0, None

        return self._clamp(score), "right"

    # ==========================================================
    # LUNGE SCORE
    # ==========================================================

    def _score_lunge(self, landmarks):
        """
        Score a lunge.

        Lunge characteristics:
            - one knee is substantially more bent
            - the other leg is relatively straighter
            - asymmetry is intentional and meaningful
        """

        right, left = self._get_knee_angles(
            landmarks
        )

        if right is None or left is None:
            return 0.0, None

        difference = abs(
            right - left
        )

        if difference < self.LUNGE_MIN_ASYMMETRY:
            return 0.0, None

        if right < left:
            bent_angle = right
            straight_angle = left
            side = "right"
        else:
            bent_angle = left
            straight_angle = right
            side = "left"

        bent_score = self._range_score(
            bent_angle,
            self.SQUAT_KNEE_START,
            self.LUNGE_DEEP_KNEE,
        )

        asymmetry_score = self._clamp(
            (
                difference
                - self.LUNGE_MIN_ASYMMETRY
            )
            / (
                self.LUNGE_STRONG_ASYMMETRY
                - self.LUNGE_MIN_ASYMMETRY
            )
        )

        # The rear/other leg should generally be straighter.
        straight_score = self._clamp(
            (
                straight_angle
                - self.LUNGE_BENT_KNEE
            )
            / 40.0
        )

        score = (
            bent_score * 0.55
            + asymmetry_score * 0.30
            + straight_score * 0.15
        )

        if bent_angle > self.LUNGE_BENT_KNEE:
            score *= 0.50

        if score < self.MIN_DETECTION_SCORE:
            return 0.0, None

        return self._clamp(score), side

    # ==========================================================
    # ALL CANDIDATES
    # ==========================================================

    def _calculate_scores(self, landmarks):
        """
        Calculate scores for every supported exercise.
        """

        squat_score, squat_side = (
            self._score_squat(landmarks)
        )

        curl_score, curl_side = (
            self._score_bicep_curl(landmarks)
        )

        lunge_score, lunge_side = (
            self._score_lunge(landmarks)
        )

        scores = {
            "squat": round(
                squat_score,
                3,
            ),
            "bicep_curl": round(
                curl_score,
                3,
            ),
            "lunge": round(
                lunge_score,
                3,
            ),
        }

        candidates = (
            (
                "squat",
                squat_score,
                squat_side,
            ),
            (
                "bicep_curl",
                curl_score,
                curl_side,
            ),
            (
                "lunge",
                lunge_score,
                lunge_side,
            ),
        )

        candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return (
            candidates,
            scores,
        )

    # ==========================================================
    # TEMPORAL CONFIRMATION
    # ==========================================================

    def _update_stability(
        self,
        exercise,
        confidence,
        side,
    ):
        """
        Require the same candidate for multiple frames.
        """

        # ------------------------------------------------------
        # No candidate.
        # ------------------------------------------------------

        if exercise is None:
            self.candidate_exercise = None
            self.candidate_side = None
            self.candidate_confidence = 0.0
            self.candidate_frames = 0

            self.lost_frames += 1

            if (
                self.current_exercise is not None
                and self.lost_frames
                <= self.LOST_FRAME_TOLERANCE
            ):
                self.current_status = "tracking"

                return {
                    "exercise": self.current_exercise,
                    "confidence": self.current_confidence,
                    "side": self.current_side,
                    "status": "tracking",
                }

            self.current_exercise = None
            self.current_confidence = 0.0
            self.current_side = None
            self.current_status = "waiting"

            return {
                "exercise": None,
                "confidence": 0.0,
                "side": None,
                "status": "waiting_for_exercise",
            }

        self.lost_frames = 0

        # ------------------------------------------------------
        # Same as current stable exercise.
        # ------------------------------------------------------

        if exercise == self.current_exercise:

            self.candidate_exercise = None
            self.candidate_frames = 0
            self.candidate_confidence = 0.0
            self.candidate_side = None

            # Smooth confidence instead of jumping around.
            self.current_confidence = (
                self.current_confidence * 0.75
                + confidence * 0.25
            )

            if side is not None:
                self.current_side = side

            self.current_status = "active"

            return {
                "exercise": self.current_exercise,
                "confidence": round(
                    self.current_confidence,
                    3,
                ),
                "side": self.current_side,
                "status": "active",
            }

        # ------------------------------------------------------
        # New candidate.
        # ------------------------------------------------------

        if exercise != self.candidate_exercise:

            self.candidate_exercise = exercise
            self.candidate_side = side
            self.candidate_confidence = confidence
            self.candidate_frames = 1

        else:

            self.candidate_frames += 1

            self.candidate_confidence = (
                self.candidate_confidence * 0.70
                + confidence * 0.30
            )

            if side is not None:
                self.candidate_side = side

        # ------------------------------------------------------
        # Candidate not yet confirmed.
        # ------------------------------------------------------

        if (
            self.candidate_frames
            < self.confirmation_frames
        ):

            self.current_status = "detecting"

            return {
                "exercise": self.current_exercise,
                "detected_exercise": exercise,
                "confidence": round(
                    confidence,
                    3,
                ),
                "side": side,
                "status": "detecting",
                "candidate_frames": self.candidate_frames,
                "required_frames": self.confirmation_frames,
            }

        # ------------------------------------------------------
        # Confirm new exercise.
        # ------------------------------------------------------

        self.current_exercise = exercise
        self.current_confidence = self._clamp(
            self.candidate_confidence
        )
        self.current_side = self.candidate_side

        self.current_status = "active"

        self.candidate_exercise = None
        self.candidate_side = None
        self.candidate_confidence = 0.0
        self.candidate_frames = 0

        return {
            "exercise": self.current_exercise,
            "detected_exercise": self.current_exercise,
            "confidence": round(
                self.current_confidence,
                3,
            ),
            "side": self.current_side,
            "status": "active",
            "candidate_frames": self.confirmation_frames,
            "required_frames": self.confirmation_frames,
        }

    # ==========================================================
    # MAIN DETECTION
    # ==========================================================

    def detect(self, landmarks):
        """
        Detect and stabilize the exercise.
        """

        # ------------------------------------------------------
        # Invalid pose.
        # ------------------------------------------------------

        if not self._has_valid_pose(landmarks):

            self.current_scores = {
                "squat": 0.0,
                "bicep_curl": 0.0,
                "lunge": 0.0,
            }

            result = self._update_stability(
                None,
                0.0,
                None,
            )

            result["candidates"] = dict(
                self.current_scores
            )

            return result

        # ------------------------------------------------------
        # Calculate all exercise scores.
        # ------------------------------------------------------

        candidates, scores = (
            self._calculate_scores(
                landmarks
            )
        )

        self.current_scores = scores

        # ------------------------------------------------------
        # Stability bonus.
        #
        # This prevents an already active exercise from being
        # replaced by a slightly stronger noisy candidate.
        # ------------------------------------------------------

        adjusted_candidates = []

        for exercise, score, side in candidates:

            adjusted_score = score

            if (
                exercise
                == self.current_exercise
            ):
                adjusted_score += (
                    self.STABILITY_BONUS
                )

            adjusted_candidates.append(
                (
                    exercise,
                    self._clamp(
                        adjusted_score
                    ),
                    side,
                )
            )

        adjusted_candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        best_exercise = None
        best_score = 0.0
        best_side = None

        if adjusted_candidates:

            (
                best_exercise,
                best_score,
                best_side,
            ) = adjusted_candidates[0]

        # ------------------------------------------------------
        # Reject weak candidate.
        # ------------------------------------------------------

        if (
            best_exercise is None
            or best_score
            < self.MIN_DETECTION_SCORE
        ):
            best_exercise = None
            best_score = 0.0
            best_side = None

        # ------------------------------------------------------
        # Update temporal state.
        # ------------------------------------------------------

        result = self._update_stability(
            best_exercise,
            best_score,
            best_side,
        )

        result["candidates"] = dict(
            self.current_scores
        )

        result["candidate_exercise"] = (
            self.candidate_exercise
        )

        result["candidate_frames"] = (
            self.candidate_frames
        )

        result["required_frames"] = (
            self.confirmation_frames
        )

        return result

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):
        return self.current_exercise

    def get_confidence(self):
        return self.current_confidence

    def get_current_side(self):
        return self.current_side

    def get_scores(self):
        return dict(
            self.current_scores
        )

    def get_candidate_exercise(self):
        return self.candidate_exercise

    def get_candidate_frames(self):
        return self.candidate_frames

    def get_status(self):
        return self.current_status

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Completely reset detector state.
        """

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        self.candidate_exercise = None
        self.candidate_side = None
        self.candidate_confidence = 0.0
        self.candidate_frames = 0

        self.lost_frames = 0

        self.current_scores = {
            "squat": 0.0,
            "bicep_curl": 0.0,
            "lunge": 0.0,
        }

        self.current_status = "waiting"