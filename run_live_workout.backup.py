"""
AI Fitness Tracker
Live Automatic Workout Launcher
"""

from ai_engine.workout.live_auto_workout import LiveAutoWorkout


def main():

    workout = LiveAutoWorkout(
        camera_index=0,
        model_path="models/pose_landmarker.task",

        # ----------------------------------------------
        # Voice
        # ----------------------------------------------

        voice_enabled=True,
        voice_confidence=0.70,
        speech_rate=175,
        speech_volume=1.0,
        speech_queue_size=20,
    )

    try:

        workout.run()

    except KeyboardInterrupt:

        print(
            "\nWorkout interrupted."
        )

    except Exception as error:

        print(
            f"\nWorkout error: {error}"
        )

    finally:

        workout.close()


if __name__ == "__main__":
    main()