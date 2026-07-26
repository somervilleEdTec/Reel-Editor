from reelwright.edit.apply_candidate import apply_candidate
from reelwright.models.word import Word
from reelwright.rank.caveats import caveat_warnings
from reelwright.rank.windows import enumerate_windows


def _mk(n=40):
    return [
        Word(id=i, text=("however" if i == 35 else f"w{i}"), start_s=i * 1.0, end_s=i * 1.0 + 0.8, source_id="s")
        for i in range(n)
    ]


def test_apply_candidate():
    words = _mk(10)
    out = apply_candidate(words, 2, 5)
    assert [w.id for w in out if not w.deleted] == [2, 3, 4, 5]


def test_claim_caveat_fixture(tmp_path):
    from pathlib import Path
    from reelwright.asr.align import import_vtt
    from reelwright.rank.caveats import caveat_warnings
    from reelwright.rank.windows import enumerate_windows

    src = Path("tests/fixtures/claim_caveat.vtt")
    words = import_vtt(str(src), "s")
    # Select only the claim span (before however)
    claim_end = next(i for i, w in enumerate(words) if w.text.lower().startswith("however")) - 1
    warns = caveat_warnings(words, 0, max(0, claim_end))
    assert warns
    cands = enumerate_windows(words, min_s=1, max_s=10)
    assert cands

