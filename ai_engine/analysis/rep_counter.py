from collections import deque


class RepCounter:
    """
    Real-time repetition counter.

    Rep cycle:
        UP -> DOWN -> UP

    Smoothing reduces camera noise, while raw angle is also
    considered so fast movements are not missed.
    """

    def __init__(
        self,
        up_threshold=150,
        down_threshold=100,
        smoothing_window=3,
        min_rep_gap=3,
    ):
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.min_rep_gap = min_rep_gap

        self.angle_history = deque(maxlen=smoothing_window)

        self.state = "UP"
        self.reps = 0

        self.reached_down = False
        self.frames_since_rep = min_rep_gap

    # ---------------------------------------------------------
    # SMOOTH ANGLE
    # ---------------------------------------------------------

    def smooth_angle(self, angle):
        self.angle_history.append(float(angle))

        return sum(self.angle_history) / len(self.angle_history)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(self, angle):

        raw_angle = float(angle)

        self.frames_since_rep += 1

        smoothed_angle = self.smooth_angle(raw_angle)

        # =====================================================
        # UP -> DOWN
        # =====================================================

        if self.state == "UP":

            if (
                smoothed_angle <= self.down_threshold
                or raw_angle <= self.down_threshold
            ):
                self.state = "DOWN"
                self.reached_down = True

        # =====================================================
        # DOWN -> UP
        # =====================================================

        elif self.state == "DOWN":

            # Use either the smoothed angle OR raw angle.
            # This prevents fast movements from being missed.
            if (
                smoothed_angle >= self.up_threshold
                or raw_angle >= self.up_threshold
            ):

                if (
                    self.reached_down
                    and self.frames_since_rep >= self.min_rep_gap
                ):
                    self.reps += 1
                    self.frames_since_rep = 0

                self.state = "UP"
                self.reached_down = False

        return {
            "angle": round(smoothed_angle, 1),
            "raw_angle": round(raw_angle, 1),
            "state": self.state,
            "reps": self.reps,
        }

    # ---------------------------------------------------------
    # GETTERS
    # ---------------------------------------------------------

    def get_state(self):
        return self.state

    def get_reps(self):
        return self.reps

    def get_smoothed_angle(self):

        if not self.angle_history:
            return None

        return round(
            sum(self.angle_history) / len(self.angle_history),
            1,
        )

    # ---------------------------------------------------------
    # RESET
    # ---------------------------------------------------------

    def reset(self):

        self.angle_history.clear()

        self.state = "UP"
        self.reps = 0

        self.reached_down = False
        self.frames_since_rep = self.min_rep_gap