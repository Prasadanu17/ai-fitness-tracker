from ai_engine.analysis.rep_counter import RepCounter


def main():

    counter = RepCounter(
        up_threshold=160,
        down_threshold=100,
        smoothing_window=3,
        min_rep_gap=5,
    )

    test_angles = [
        170,
        150,
        120,
        90,
        60,
        80,
        110,
        140,
        160,
        170,
    ]

    print("Rep Counter Test")
    print("----------------")

    for angle in test_angles:

        result = counter.update(angle)

        print(
            f"Angle: {angle:3}° | "
            f"Smoothed: {result['angle']:5.1f}° | "
            f"State: {result['state']:4} | "
            f"Reps: {result['reps']}"
        )

    print()
    print(f"Final reps: {counter.get_reps()}")


if __name__ == "__main__":
    main()