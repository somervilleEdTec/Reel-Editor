from __future__ import annotations

from typing import Protocol

from reelwright.models.word import Word


class TranscriptionBackend(Protocol):
    def transcribe(self, path: str, source_id: str) -> list[Word]:
        ...
