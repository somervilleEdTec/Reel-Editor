// Mirrors src/reelwrite/media_formats.py — keep both in sync.
export const VIDEO_EXTS = [
  "mp4", "mov", "mkv", "webm", "m4v", "avi",
  "mts", "m2ts", "wmv", "flv", "3gp", "ts",
];

const VIDEO_RE = new RegExp(`\\.(${VIDEO_EXTS.join("|")})$`, "i");
export const isVideoName = (name) => VIDEO_RE.test(name || "");

// Fallback when GET /formats is unavailable.
export const OUTPUT_FORMATS = [
  { key: "mp4", ext: ".mp4", label: "MP4 · H.264/AAC" },
  { key: "mov", ext: ".mov", label: "MOV · H.264/AAC" },
  { key: "webm", ext: ".webm", label: "WebM · VP9/Opus" },
  { key: "mkv", ext: ".mkv", label: "MKV · H.264/AAC" },
];
