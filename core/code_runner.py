import requests

def run_code(language: str, code: str, stdin: str = ""):
    """
    Run code in the given language using Piston API (emkc.org).
    """
    url = "https://emkc.org/api/v2/piston/execute"

    payload = {
        "language": language,
        "version": "*",
        "files": [{"name": f"main.{language}", "content": code}],
        "stdin": stdin
    }

    try:
        response = requests.post(url, json=payload)
        result = response.json()

        if "run" in result:
            stdout = result["run"].get("stdout", "")
            stderr = result["run"].get("stderr", "")
            return stdout if stdout else stderr
        else:
            return f"Unexpected response: {result}"
    except Exception as e:
        return f"Error: {e}"
