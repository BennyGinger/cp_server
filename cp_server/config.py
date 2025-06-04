from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
if not ROOT.exists():
    raise FileNotFoundError(f"Root directory {ROOT!r} does not exist. Please check your setup.")

