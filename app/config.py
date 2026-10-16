
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
TESTS_DIR = PROJECT_ROOT / "tests"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 40
DEFAULT_TOP_K = 5

for directory in (
    DOCUMENTS_DIR,
    PROCESSED_DIR,
    LOGS_DIR,
    TESTS_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)
