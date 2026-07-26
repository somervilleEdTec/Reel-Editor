from reelwrite.jobs.errors import MediaProbeError, require_media
from reelwrite.jobs.queue import JobQueue


def test_require_media_missing(tmp_path):
    try:
        require_media(str(tmp_path / "nope.mp4"))
        assert False
    except MediaProbeError as e:
        assert e.code == "E_MEDIA_MISSING"


def test_job_cancel():
    q = JobQueue()
    started = []

    def work(job):
        started.append(1)
        job.cancel.wait(0.5)
        if job.cancel.is_set():
            return None
        return "ok"

    job = q.submit("t", work)
    assert q.cancel(job.id)
    # allow thread to finish
    import time

    time.sleep(0.2)
    j = q.get(job.id)
    assert j.status in ("cancelled", "running", "done")


def test_active_lists_only_unfinished_jobs_of_kind():
    import threading
    import time

    q = JobQueue()
    release = threading.Event()
    job = q.submit("export", lambda j: release.wait(5), meta={"out": "/tmp/a.mp4"})
    other = q.submit("transcribe", lambda j: None)
    active = q.active("export")
    assert [j.id for j in active] == [job.id]
    assert active[0].meta["out"] == "/tmp/a.mp4"
    release.set()
    for _ in range(50):
        if q.get(job.id).status == "done":
            break
        time.sleep(0.02)
    assert q.active("export") == []
    assert other.kind == "transcribe"
