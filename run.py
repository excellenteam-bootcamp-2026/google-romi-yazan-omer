import sys

from src.main import DEFAULT_ROOT_PATH, run

if __name__ == "__main__":
    root_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT_PATH
    run(root_path)
