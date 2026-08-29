from ai_engine.live_auto_workout import LiveAutoWorkout


def main():
    workout = LiveAutoWorkout()

    try:
        workout.run()
    except KeyboardInterrupt:
        print("\nWorkout interrupted.")
        workout.stop()
    except Exception as error:
        print(f"\nWorkout error: {error}")
        workout.stop()


if __name__ == "__main__":
    main()