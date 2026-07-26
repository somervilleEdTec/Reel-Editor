from __future__ import annotations

import os

from reelwrite.models.word import Word


class AzureSpeechBackend:
    """Opt-in Azure Speech STT. Requires AZURE_SPEECH_KEY + REGION."""

    def transcribe(self, path: str, source_id: str) -> list[Word]:
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION")
        if not key or not region:
            raise RuntimeError(
                "Azure Speech not configured. Set AZURE_SPEECH_KEY and "
                "AZURE_SPEECH_REGION (EU region recommended). Local Whisper is default."
            )
        raise RuntimeError(
            "Azure Speech SDK call not available in this environment; "
            "configure azure-cognitiveservices-speech when keys are provisioned."
        )
