from __future__ import annotations

from urllib.parse import urlparse


def assert_azure_openai_endpoint(endpoint: str) -> str:
    """Allow only https Azure OpenAI-style endpoints (blocks file/ssrf schemes)."""
    raw = (endpoint or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("AZURE_OPENAI_ENDPOINT must use https")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("AZURE_OPENAI_ENDPOINT host missing")
    ok = (
        host.endswith(".openai.azure.com")
        or host.endswith(".cognitiveservices.azure.com")
        or host == "openai.azure.com"
    )
    if not ok:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT host must be *.openai.azure.com "
            "or *.cognitiveservices.azure.com"
        )
    return raw.rstrip("/")
