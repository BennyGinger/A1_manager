import sys
from pathlib import Path

# Ermittle das Projektstammverzeichnis (z.B. zwei Ebenen höher, falls Tests in tests/a1_manager liegen)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))