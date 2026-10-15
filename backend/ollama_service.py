"""
Ollama Service module for Orderly AI.
Handles local HTTP communication with Ollama server, health checks,
model listing, and JSON completions with Gemma 3.
"""

from typing import Dict, List, Tuple, Optional, Any
import requests
from backend.config import DEFAULT_OLLAMA_URL, DEFAULT_MODEL, OLLAMA_TIMEOUT


def check_ollama_status(
    base_url: str = DEFAULT_OLLAMA_URL,
    target_model: str = DEFAULT_MODEL,
    timeout: float = 3.0,
) -> Dict[str, Any]:
    """
    Checks if Ollama is running locally and inspects available models.
    Returns status dictionary with connection state and model availability.
    """
    clean_url = base_url.rstrip("/")
    result = {
        "connected": False,
        "base_url": clean_url,
        "models": [],
        "has_target_model": False,
        "target_model": target_model,
        "version": None,
        "error_message": None,
    }

    try:
        # Check /api/tags
        tags_response = requests.get(f"{clean_url}/api/tags", timeout=timeout)
        if tags_response.status_code == 200:
            result["connected"] = True
            data = tags_response.json()
            models_list = data.get("models", [])
            model_names = [m.get("name", "") for m in models_list]
            result["models"] = model_names

            clean_target = target_model.strip().lower()
            target_prefix = clean_target.split(":")[0]
            result["has_target_model"] = any(
                clean_target == m.lower() or (target_prefix and m.lower().startswith(target_prefix))
                for m in model_names
            )

        # Check /api/version if available
        try:
            ver_resp = requests.get(f"{clean_url}/api/version", timeout=timeout)
            if ver_resp.status_code == 200:
                result["version"] = ver_resp.json().get("version")
        except Exception:
            pass

    except requests.exceptions.ConnectionError:
        result["error_message"] = (
            f"Cannot connect to Ollama at {clean_url}. "
            "Please ensure Ollama is installed and running (`ollama serve`)."
        )
    except requests.exceptions.Timeout:
        result["error_message"] = f"Connection to Ollama at {clean_url} timed out."
    except Exception as exc:
        result["error_message"] = f"Unexpected error connecting to Ollama: {str(exc)}"

    return result


def generate_local_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    timeout: int = OLLAMA_TIMEOUT,
    format_type: str = "json",
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Calls local Ollama /api/generate endpoint with JSON output mode.
    Returns: (success: bool, response_text: str | None, error_message: str | None)
    """
    clean_url = base_url.rstrip("/")
    endpoint = f"{clean_url}/api/generate"

    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for strict factual extraction
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    if format_type == "json":
        payload["format"] = "json"

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            return True, response_text, None

        if response.status_code == 404:
            return (
                False,
                None,
                f"Model '{model}' is not installed in Ollama. "
                f"Run `ollama pull {model}` in your terminal to install it.",
            )

        return (
            False,
            None,
            f"Ollama returned HTTP {response.status_code}: {response.text}",
        )

    except requests.exceptions.ConnectionError:
        return (
            False,
            None,
            f"Ollama is not reachable at {clean_url}. "
            "Make sure the Ollama application or background service is running.",
        )
    except requests.exceptions.Timeout:
        return (
            False,
            None,
            f"Ollama inference timed out after {timeout} seconds. "
            "The model might still be loading or system is under heavy load.",
        )
    except Exception as exc:
        return (
            False,
            None,
            f"Failed to communicate with Ollama: {str(exc)}",
        )
