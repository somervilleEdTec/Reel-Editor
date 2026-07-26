export async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(errorMessage(text) || res.statusText);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

/** FastAPI errors arrive as JSON {"detail": ...} — surface the detail text. */
function errorMessage(text) {
  try {
    const d = JSON.parse(text)?.detail;
    if (typeof d === "string") return d;
    if (d != null) return JSON.stringify(d);
  } catch {
    /* not JSON */
  }
  return text;
}

export const get = (path) => api(path);
export const post = (path, body) => api(path, { method: "POST", body: JSON.stringify(body ?? {}) });
