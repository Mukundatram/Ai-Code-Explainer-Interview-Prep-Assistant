import subprocess
import tempfile
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── JDoodle language map ──────────────────────────────────────────────────────
# Maps Streamlit-ace language names → (jdoodle_language, versionIndex)
JDOODLE_LANG_MAP = {
    "javascript": ("nodejs",      "4"),
    "typescript": ("typescript",  "0"),
    "java":       ("java",        "4"),
    "cpp":        ("cpp17",       "0"),
    "c":          ("c",           "5"),
    "go":         ("go",          "4"),
    "rust":       ("rust",        "4"),
    "php":        ("php",         "4"),
    "ruby":       ("ruby",        "4"),
    "kotlin":     ("kotlin",      "3"),
    "swift":      ("swift",       "4"),
    "r":          ("r",           "4"),
    "scala":      ("scala",       "4"),
    "perl":       ("perl",        "4"),
    "bash":       ("bash",        "4"),
    "sql":        ("sql",         "4"),
    "lua":        ("lua",         "4"),
    "haskell":    ("haskell",     "4"),
}

# File extensions for local temp-file execution (future use)
EXT_MAP = {
    "python": "py",
    "javascript": "js",
    "java": "java",
    "cpp": "cpp",
}


def _run_python_local(code: str, stdin: str = "") -> str:
    """
    Execute Python code locally using subprocess — no API required.
    Runs in an isolated temp file with a 10-second timeout.
    """
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ["python", tmp_path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=10,
        )
        os.unlink(tmp_path)

        if result.stdout:
            return result.stdout
        if result.stderr:
            return result.stderr
        return "(no output)"

    except subprocess.TimeoutExpired:
        return "⏰ Execution timed out (10s limit)."
    except FileNotFoundError:
        return "❌ Python interpreter not found. Make sure Python is in PATH."
    except Exception as e:
        return f"❌ Local execution error: {e}"


def _run_jdoodle(language: str, code: str, stdin: str = "") -> str:
    """
    Execute code via JDoodle API.
    Requires JDOODLE_CLIENT_ID and JDOODLE_CLIENT_SECRET in .env
    Free tier: 200 executions / day — https://www.jdoodle.com/compiler-api/
    """
    client_id     = os.getenv("JDOODLE_CLIENT_ID", "")
    client_secret = os.getenv("JDOODLE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return (
            "⚠️ JDoodle API keys not configured.\n"
            "Add JDOODLE_CLIENT_ID and JDOODLE_CLIENT_SECRET to your .env file.\n"
            "Get a free key at: https://www.jdoodle.com/compiler-api/"
        )

    jdoodle_lang, version_idx = JDOODLE_LANG_MAP.get(language, (language, "0"))

    payload = {
        "clientId":     client_id,
        "clientSecret": client_secret,
        "script":       code,
        "language":     jdoodle_lang,
        "versionIndex": version_idx,
        "stdin":        stdin,
    }

    try:
        resp = requests.post(
            "https://api.jdoodle.com/v1/execute",
            json=payload,
            timeout=15,
        )
        data = resp.json()

        if "output" in data:
            return data["output"]
        elif "error" in data:
            return f"JDoodle error: {data['error']}"
        else:
            return f"Unexpected response: {data}"

    except requests.Timeout:
        return "⏰ JDoodle request timed out."
    except Exception as e:
        return f"❌ JDoodle error: {e}"


def run_code(language: str, code: str, stdin: str = "") -> str:
    """
    Run code in the given language.

    Strategy:
      • Python  → local subprocess (fast, unlimited, no API key needed)
      • Others  → JDoodle API (free tier, needs JDOODLE_CLIENT_ID/SECRET in .env)
    """
    lang = language.lower().strip()

    if lang == "python":
        return _run_python_local(code, stdin)
    else:
        return _run_jdoodle(lang, code, stdin)
