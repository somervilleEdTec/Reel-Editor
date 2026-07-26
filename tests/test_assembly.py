from reelwright.assembly.distribute import auto_distribute, reorder_clips
from reelwright.assembly.reconcile import clip_output_duration, reconcile
from reelwright.edit.edl import derive_edl
from reelwright.edit.timeline import Timeline
from reelwright.models.assembly import Assembly, AssemblyClip
from reelwright.models.source import Source
from reelwright.models.word import Word


def test_auto_distribute():
    words = [
        Word(id=i, text=f"w{i}", start_s=i * 0.5, end_s=i * 0.5 + 0.4, source_id="vo")
        for i in range(12)
    ]
    clips = [
        Source(id="c1", path="a.mp4", role="media", duration_s=5),
        Source(id="c2", path="b.mp4", role="media", duration_s=5),
        Source(id="c3", path="c.mp4", role="media", duration_s=5),
    ]
    asm = auto_distribute("vo", clips, words)
    assert len(asm.clips) == 3
    assert asm.clips[0].word_start_id == 0
    assert asm.clips[-1].word_end_id == 11


def test_reorder_proportional():
    asm = Assembly(
        narration_source_id="vo",
        clips=[
            AssemblyClip(id="a", source_id="c1", word_start_id=0, word_end_id=3),
            AssemblyClip(id="b", source_id="c2", word_start_id=4, word_end_id=7),
        ],
    )
    out = reorder_clips(asm, ["b", "a"])
    assert out.clips[0].id == "b"
    assert out.clips[0].word_start_id == 0


def test_reconcile_slow_warns():
    clip = AssemblyClip(
        id="x", source_id="c", in_s=0, word_start_id=0, word_end_id=1,
        duration_strategy="slow",
    )
    src = Source(id="c", path="a.mp4", role="media", duration_s=1.0)
    updated, warns = reconcile(clip, src, needed_s=3.0)
    assert updated.speed < 0.5
    assert warns
