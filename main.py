from screenshots_cloudera import run_all
from screenshots_kibana import run
import os
import argparse

OUTPUT_DIR = "output"

if os.path.exists(OUTPUT_DIR):
    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take screenshots from Kibana and Cloudera dashboards")
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run browser with visible UI"
    )
    args = parser.parse_args()
    
    print(f"Running in {'headless' if args.headless else 'visible'} mode...")
    run_all(headless=args.headless)
    run(headless=args.headless)