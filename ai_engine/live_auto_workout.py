def process_frame(self, frame):
    """
    Process one webcam frame safely.

    A frame is only passed to the workout engine when
    a usable pose has been detected.
    """

    if self.pose_engine is None:
        raise RuntimeError(
            "Pose engine is not initialized."
        )

    if self.workout_engine is None:
        raise RuntimeError(
            "Workout engine is not initialized."
        )

    if frame is None:
        return self._waiting_result()

    # ----------------------------------------------------------
    # Validate frame
    # ----------------------------------------------------------

    if not hasattr(frame, "shape"):
        return self._waiting_result()

    if len(frame.shape) != 3:
        return self._waiting_result()

    height, width = frame.shape[:2]

    if height <= 0 or width <= 0:
        return self._waiting_result()

    # ----------------------------------------------------------
    # MediaPipe
    # ----------------------------------------------------------

    pose_results = self.pose_engine.process_frame(frame)

    if pose_results is None:
        return self._waiting_result()

    # ----------------------------------------------------------
    # Extract landmarks
    # ----------------------------------------------------------

    landmarks = self.pose_engine.get_landmarks(
        pose_results
    )

    # ----------------------------------------------------------
    # No person detected
    # ----------------------------------------------------------

    if landmarks is None:
        return self._waiting_result()

    # ----------------------------------------------------------
    # Validate landmark count
    #
    # MediaPipe Pose normally provides 33 landmarks.
    # ----------------------------------------------------------

    if len(landmarks) < 33:
        return self._waiting_result()

    # ----------------------------------------------------------
    # Validate landmark objects
    # ----------------------------------------------------------

    required_indexes = [
        11, 12, 13, 14, 15, 16,
        23, 24, 25, 26, 27, 28,
    ]

    for index in required_indexes:

        landmark = landmarks[index]

        if landmark is None:
            return self._waiting_result()

        if not hasattr(landmark, "x"):
            return self._waiting_result()

        if not hasattr(landmark, "y"):
            return self._waiting_result()

    # ----------------------------------------------------------
    # Valid pose
    # ----------------------------------------------------------

    return self.workout_engine.process(
        landmarks
    )