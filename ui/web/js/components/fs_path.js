/** Strip Explorer "Copy as path" quotes, BOM, and file:// wrappers. */
export function normalizePastedPath(raw) {
  let s = String(raw || "").trim().replace(/^\uFEFF/, "").trim();
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    s = s.slice(1, -1).trim();
  }
  if (/^file:/i.test(s)) {
    try {
      const u = new URL(s);
      s = decodeURIComponent(u.pathname || "");
      if (/^\/[A-Za-z]:\//.test(s)) s = s.slice(1);
    } catch { /* keep s */ }
  }
  return s;
}

/** True when text looks like a filesystem path, not a UI status label. */
export function looksLikePath(raw) {
  const s = normalizePastedPath(raw);
  if (!s) return false;
  if (/^\d+\s+\w*selected\w*$/i.test(s)) return false;
  if (/selected$/i.test(s) && !/[\\/]/.test(s)) return false;
  return /[\\/]/.test(s) || /^[A-Za-z]:/.test(s) || s.startsWith("~");
}

/** Build breadcrumb segments { label, path } for a directory string. */
export function crumbSegments(dir) {
  if (!dir) return [];
  const sep = dir.includes("\\") ? "\\" : "/";
  const parts = dir.split(/[\\/]/).filter(Boolean);
  const segs = [];
  let acc = dir.startsWith("/") ? "" : null;

  if (acc === "") {
    segs.push({ label: sep, path: sep });
  }

  // UNC: \\server\share\...
  if (/^\\\\/.test(dir) || /^\/\//.test(dir)) {
    const uncRoot = `${sep}${sep}${parts[0] || ""}${sep}${parts[1] || ""}`;
    if (parts.length >= 2) {
      segs.push({ label: `${sep}${sep}${parts[0]}`, path: uncRoot });
      acc = uncRoot;
      parts.slice(2).forEach((part, i) => {
        acc = `${acc}${sep}${part}`;
        segs.push({ label: part, path: acc });
      });
      return segs;
    }
  }

  parts.forEach((part, i) => {
    acc = acc === null ? part : `${acc}${sep}${part}`;
    const path = acc + (i === 0 && part.endsWith(":") ? sep : "");
    segs.push({ label: part, path });
  });
  return segs;
}

export function fmtSize(n) {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = n;
  let i = -1;
  do {
    v /= 1024;
    i += 1;
  } while (v >= 1024 && i < units.length - 1);
  return `${v >= 10 ? Math.round(v) : v.toFixed(1)} ${units[i]}`;
}
