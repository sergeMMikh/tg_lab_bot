from pathlib import Path

def read_token(path: str | Path) -> str:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")

    token = path.read_text(encoding="utf-8").strip()

    if not token:
        raise ValueError("Token file is empty")

    return token