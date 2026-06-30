import argparse
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


# Resolve the project root so the script works from any current directory.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.lifecycle import init_db, reset_db


API_URL = "http://127.0.0.1:8000"
DASHBOARD_URL = "http://127.0.0.1:8501"


def start_process(command: list[str]) -> subprocess.Popen:
    # Run child services from the project root so package imports stay stable.
    return subprocess.Popen(command, cwd=ROOT_DIR)


def stop_processes(processes: list[subprocess.Popen]) -> None:
    # Ask services to stop first, then force-kill anything that is still alive.
    for process in processes:
        if process.poll() is None:
            stop_process_tree(process)

    time.sleep(1)

    for process in processes:
        if process.poll() is None:
            stop_process_tree(process, force=True)


def stop_process_tree(process: subprocess.Popen, force: bool = False) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    if force:
        process.kill()
    else:
        process.terminate()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the hotel pricing demo.")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset and reseed the SQLite database before starting services.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the API docs and dashboard in your browser.",
    )
    args = parser.parse_args()

    if args.reset_db:
        reset_db()
        print("Reset SQLite demo database.")
    else:
        # init_db is non-destructive: it creates tables and seeds only if empty.
        init_db()
        print("Initialized SQLite demo database.")

    # Start API and dashboard as sibling processes under this launcher.
    # Keeping both attached here lets Ctrl+C stop the whole demo cleanly.
    processes = [
        start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ]
        ),
        start_process(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/dashboard/streamlit_app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                "8501",
                "--server.headless",
                "true",
            ]
        ),
    ]

    print(f"FastAPI docs: {API_URL}/docs")
    print(f"Dashboard: {DASHBOARD_URL}")
    print("Press Ctrl+C to stop both services.")

    if args.open:
        # Give both local servers a short moment to bind their ports.
        time.sleep(3)
        webbrowser.open(f"{API_URL}/docs")
        webbrowser.open(DASHBOARD_URL)

    def handle_stop(signum, frame) -> None:
        # Handle Ctrl+C and normal termination with the same cleanup path.
        stop_processes(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    try:
        # If either service exits, stop the other one so the demo does not
        # leave a half-running API or dashboard behind.
        while all(process.poll() is None for process in processes):
            time.sleep(1)
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    main()
