import sys
from pathlib import Path

# Determine the project root directory – in this case two levels above conftest.py,
# if conftest.py is located directly in the tests directory.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))