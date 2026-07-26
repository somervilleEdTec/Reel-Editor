from __future__ import annotations

import sys

from reelwright.models.word import Word


class LocalWhisper:
    def __init__(self, model_size: str = "distil-large-v3", device: str = "cpu"):
        self.model_size = model_size
        self.device = device

    def transcribe(self, path: str, source_id: str) -> list[Word]:
        from faster_whisper import WhisperModel

        print(f"Loading Whisper {self.model_size}…", file=sys.stderr)
        model = WhisperModel(self.model_size, device=self.device, compute_type="int8")
        segments, _ = model.transcribe(path, word_timestamps=True, language="en")
        words: list[Word] = []
        wid = 0
        for seg in segments:
            for w in seg.words or []:
                words.append(
                    Word(
                        id=wid,
                        text=w.word.strip(),
                        start_s=float(w.start),
                        end_s=float(w.end),
                        source_id=source_id,
                    )
                )
                wid += 1
                if wid % 50 == 0:
                    print(f"  words={wid}", file=sys.stderr)
        return words
