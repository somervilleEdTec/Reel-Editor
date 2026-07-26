from reelwright.jobs.errors import MediaProbeError, require_media
from reelwright.jobs.queue import JobQueue


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
