import os
from typing import Tuple

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv():
        pass

REQUIRED_ENV = ["GITHUB_TOKEN", "OPENAI_API_KEY"]

def load_and_validate_env() -> Tuple[bool, list]:
    load_dotenv()
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    return (len(missing)==0, missing)
