import sys
from pathlib import Path

# make `app` importable from the backend package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
