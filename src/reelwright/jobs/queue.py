from __future__ import annotations

import threading
import time
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
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, kind: str, fn: Callable[[Job], Any]) -> Job:
        job = Job(id=str(uuid.uuid4()), kind=kind)
        with self._lock:
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


QUEUE = JobQueue()
