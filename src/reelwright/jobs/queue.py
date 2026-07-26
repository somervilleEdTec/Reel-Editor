from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"  # queued|running|done|error|cancelled
    progress: float = 0.0
    error: str | None = None
    result: Any = None
    cancel: threading.Event = field(default_factory=threading.Event)


class JobQueue:
    def __init__(self, max_jobs: int = 64):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs

    def submit(self, kind: str, fn: Callable[[Job], Any]) -> Job:
        job = Job(id=str(uuid.uuid4()), kind=kind)
        with self._lock:
            self._prune_locked()
            if len(self._jobs) >= self._max_jobs:
                raise RuntimeError("Too many jobs queued; cancel or wait")
            self._jobs[job.id] = job

        def runner():
            job.status = "running"
            try:
                if job.cancel.is_set():
                    job.status = "cancelled"
                    return
                job.result = fn(job)
                if job.cancel.is_set():
                    job.status = "cancelled"
                else:
                    job.status = "done"
                    job.progress = 1.0
            except Exception as e:
                job.status = "error"
                job.error = str(e)

        threading.Thread(target=runner, daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.cancel.set()
        if job.status == "queued":
            job.status = "cancelled"
        return True

    def _prune_locked(self) -> None:
        done = {
            jid
            for jid, j in self._jobs.items()
            if j.status in ("done", "error", "cancelled")
        }
        # Keep a small history; drop oldest finished first when near cap.
        if len(self._jobs) - len(done) + 1 < self._max_jobs and len(done) < 32:
            return
        for jid in list(done)[: max(0, len(self._jobs) - self._max_jobs + 1)]:
            self._jobs.pop(jid, None)


QUEUE = JobQueue()
