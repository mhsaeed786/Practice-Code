"""Shared helpers for the Ollama web-scraper / campaign-mail scripts.

Each scraper script stays runnable standalone; they just import this module
for the boilerplate that was previously copy-pasted between them:
  - a timeout-aware HTTP GET wrapper (browser-like User-Agent)
  - a URL query-quoting helper for DuckDuckGo searches
  - an Ollama chat-call helper with uniform model default and error handling
"""

from urllib.parse import quote

import requests

try:
    import ollama
except ImportError:  # allow importing this module without ollama installed
    ollama = None

DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_TIMEOUT = 10

USER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    ),
}


def quote_query(query):
    """URL-encode a search query for use in a query string."""
    return quote(query)


def http_get(url, timeout=DEFAULT_TIMEOUT):
    """GET a URL with a browser-like User-Agent and a hard timeout.

    Returns the response object on success, or None on any network error.
    """
    try:
        response = requests.get(url, headers=USER_HEADERS, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"HTTP error fetching {url}: {e}")
        return None


def ollama_chat(messages, model=DEFAULT_MODEL):
    """Call ollama.chat and return the assistant message content, or None on failure."""
    if ollama is None:
        print("ollama package is not installed")
        return None
    try:
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Ollama API error: {e}")
        return None


def build_messages(system_msg, user_msg):
    """Standard [system, user] message pair for single-shot Ollama calls."""
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
