from __future__ import annotations

import json
import os
from urllib import request

from reelwright.models.word import Word
from reelwright.security.egress import assert_azure_openai_endpoint


CRITERIA = [
    "complete_idea",
    "standalone_comprehensible",
    "accurate_when_separated",
    "no_missing_caveats",
]


class AzureOpenAIRanker:
    def score_window(self, words: list[Word], start_id: int, end_id: int) -> dict:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        key = os.environ.get("AZURE_OPENAI_API_KEY")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        if not (endpoint and key and deployment):
            raise RuntimeError(
                "Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT. "
                "This sends transcript text off-device — opt-in only."
            )
        try:
            endpoint = assert_azure_openai_endpoint(endpoint)
        except ValueError as e:
            raise RuntimeError(str(e)) from e
        if "/" in deployment or "\\" in deployment or ".." in deployment:
            raise RuntimeError("Invalid AZURE_OPENAI_DEPLOYMENT name")
        text = " ".join(
            w.text for w in words if start_id <= w.id <= end_id and not w.deleted
        )
        prompt = (
            "Score this research-communication clip 0-1 for each key. "
            "Return JSON only.\nKeys: "
            + ", ".join(CRITERIA)
            + f"\n\nTEXT:\n{text}"
        )
        url = (
            f"{endpoint}/openai/deployments/{deployment}/chat/completions"
            f"?api-version=2024-02-15-preview"
        )
        body = json.dumps(
            {
                "messages": [
                    {"role": "system", "content": "You are a careful research editor."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            }
        ).encode()
        req = request.Request(
            url, data=body, headers={"api-key": key, "Content-Type": "application/json"}
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI ranking failed: {e}") from e
