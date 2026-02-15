from adbw.app import main
from adbw.errors import AdbWizardError


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    except AdbWizardError as e:
        print(f"\nError: {e}")

