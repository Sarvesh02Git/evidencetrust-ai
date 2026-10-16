
import importlib
import os
from typing import Any



from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)


def get_groq_client() -> Any:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to your local .env file."
        )

    try:
        groq = importlib.import_module("groq")
    except ModuleNotFoundError as exc:
        if exc.name == "groq":
            raise RuntimeError(
                "The 'groq' package is required. Install it with 'pip install groq'."
            ) from exc
        raise

    return groq.Groq(api_key=api_key)
