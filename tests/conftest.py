import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent / "a1_manager"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
print("Package root added to sys.path:", project_root)