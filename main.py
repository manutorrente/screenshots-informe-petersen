from screenshots_cloudera import run_all
from screenshots_kibana import run
import os

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
    run_all()
    run()