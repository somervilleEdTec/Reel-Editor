/** Convert output time → source time using EDL segments. Returns null if in a gap. */
export function outToSrc(t, segs) {
  for (const s of segs) {
    if (t >= s.output_start && t <= s.output_end + 0.001)
      return s.source_start + (t - s.output_start);
  }
  return null;
}

/** Convert source time → output time. Returns null if in a deleted region. */
export function srcToOut(t, segs) {
  for (const s of segs) {
    if (t >= s.source_start && t <= s.source_end + 0.001)
      return s.output_start + (t - s.source_start);
  }
  return null;
}

/** Total output duration from EDL. */
export function edlDuration(edl) {
  if (!edl?.segments?.length) return null;
  return edl.total_duration ?? edl.segments.at(-1)?.output_end ?? 0;
}

/** Find next kept segment starting after srcTime (for skip-deleted playback). */
export function nextKeptSeg(srcTime, segs) {
  return segs.find((s) => s.source_start > srcTime + 0.05) || null;
}

/** Build list of deleted source gaps between kept segments. */
export function deletedGaps(segs) {
  const gaps = [];
  for (let i = 0; i < segs.length - 1; i++) {
    const a = segs[i], b = segs[i + 1];
    if (b.source_start > a.source_end + 0.01)
      gaps.push({ source_start: a.source_end, source_end: b.source_start,
                  output_at: a.output_end });
  }
  return gaps;
}
