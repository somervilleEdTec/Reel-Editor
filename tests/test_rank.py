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


def test_windows_and_caveats():
    words = _mk(40)
    cands = enumerate_windows(words, min_s=5, max_s=12)
    assert cands
    warns = caveat_warnings(words, 0, 30)
    assert any("caveat" in w.lower() or "however" in w.lower() for w in warns)
