# Entry point of the application
from ui.streamlit_interface import run_ui


def main():
    print("Starting ChatDB...")
    run_ui()


if __name__ == "__main__":
    main()