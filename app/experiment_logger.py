
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import LOGS_DIR


class ExperimentLogger:
    def __init__(self, filename: str = "experiments.jsonl"):
        self.path = LOGS_DIR / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, record: dict) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **record,
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(entry, ensure_ascii=False, default=str)
                + "\n"
            )
