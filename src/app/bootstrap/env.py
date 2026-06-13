import os
import sys
from pathlib import Path

def load_dotenv() -> None:
    """
    Manually parses a .env file if it exists, without requiring python-dotenv.
    Searches from current working dir and file parent paths.
    Does not override existing environment variables.
    """
    search_dirs = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parent.parent.parent
    ]
    
    seen = set()
    unique_dirs = []
    for d in search_dirs:
        try:
            resolved = d.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_dirs.append(resolved)
        except Exception:
            pass
            
    for directory in unique_dirs:
        dotenv_path = directory / ".env"
        if dotenv_path.is_file():
            try:
                with open(dotenv_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip()
                            if val.startswith('"') and val.endswith('"'):
                                val = val[1:-1]
                            elif val.startswith("'") and val.endswith("'"):
                                val = val[1:-1]
                            if " #" in val:
                                val = val.split(" #", 1)[0].strip()
                            
                            if key and not os.environ.get(key):
                                os.environ[key] = val
                print(f"[ENV LOADER] Loaded environment variables from {dotenv_path}", file=sys.stderr, flush=True)
                break
            except Exception as e:
                print(f"[ENV LOADER] Error reading {dotenv_path}: {e}", file=sys.stderr, flush=True)
