from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_BLOCKED = (
    re.compile(r"^/etc(/|$)", re.I),
    re.compile(r"^/proc(/|$)", re.I),
    re.compile(r"^/sys(/|$)", re.I),
    re.compile(r"^/dev(/|$)", re.I),
    re.compile(r"^[A-Za-z]:\\Windows([\\/]|$)", re.I),
    re.compile(r"^[A-Za-z]:\\Program Files([\\/]|$)", re.I),
)


class PathDenied(ValueError):
    """Raised when a user path escapes the workspace sandbox."""


def workspace_roots() -> list[Path]:
    raw = os.environ.get("REELWRITE_ROOT")
    if raw:
        return [Path(raw).expanduser().resolve()]
    roots = [Path.cwd().resolve(), Path.home().resolve()]
    tmp = Path(tempfile.gettempdir()).resolve()
    if tmp not in roots:
        roots.append(tmp)
    return roots


def resolve_workspace_path(
    path: str, *, must_exist: bool = False, for_write: bool = False
) -> Path:
    """Resolve *path* into an allowed root; reject system/escaped paths."""
    if not path or "\x00" in path:
        raise PathDenied("Invalid path")
    from reelwrite.paths import normalize_user_path

    try:
        p = normalize_user_path(path)
    except ValueError as e:
        raise PathDenied(str(e)) from e
    roots = workspace_roots()
    resolved = p.resolve(strict=False) if p.is_absolute() else (roots[0] / p).resolve()
    _assert_allowed(resolved, roots)
    if must_exist and not resolved.exists():
        raise FileNotFoundError(str(resolved))
    if for_write:
        parent = resolved.parent
        if not parent.exists():
            raise PathDenied(f"Parent directory missing: {parent}")
        _assert_allowed(parent.resolve(), roots)
    return resolved


def _assert_allowed(path: Path, roots: list[Path]) -> None:
    text = str(path)
    for pat in _BLOCKED:
        if pat.search(text):
            raise PathDenied(f"Blocked system path: {path}")
    for root in roots:
        try:
            path.relative_to(root)
            return
        except ValueError:
            continue
    raise PathDenied(f"Path outside allowed workspace roots: {path}")
