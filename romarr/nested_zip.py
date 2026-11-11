"""Bounded inspection of ZIP files stored inside ZIP downloads.

Only inner ZIP containers are staged. Playable members remain in their owning
archive and use ROMarr's existing streaming hash/copy implementation.
"""

from __future__ import annotations

import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

MAX_ZIP_LAYERS = 3
MAX_INNER_ARCHIVES = 16
MAX_ZIP_MEMBERS = 10_000
MAX_INNER_BYTES = 256 * 1024 * 1024
MAX_STAGED_BYTES = 512 * 1024 * 1024
MAX_FINAL_MEMBER_BYTES = 64 * 1024 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 10_000
MAX_DESCRIPTOR_BYTES = 2 * 1024 * 1024
COPY_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class ZipLeaf:
    """A playable candidate's original member name and owning ZIP container."""

    archive_path: Path
    member: str
    size: int


class NestedZipIndex:
    """Inspect nested ZIPs with explicit bounds and temporary-file ownership.

    The caller retains this object during preview/import and thereby retains
    temporary inner-archive containers. Temporary data is removed by close()
    or when the underlying TemporaryDirectory object is garbage-collected.
    """

    def __init__(self, outer: Path, safe_name: Callable[[str, Path], bool]):
        self.members: dict[str, ZipLeaf] = {}
        self._safe_name = safe_name
        self._temp = tempfile.TemporaryDirectory(prefix="romarr-nested-zip-")
        self._inner_count = 0
        self._staged_bytes = 0
        self._examined = 0
        self._expanded_bytes = 0
        try:
            self._scan(outer, "", 1)
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        """Release only the scratch directory created by this index."""
        self._temp.cleanup()

    def _scan(self, path: Path, prefix: str, depth: int) -> None:
        """Index one ZIP without mixing leaf members from different ZIPs."""
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                self._examined += 1
                if self._examined > MAX_ZIP_MEMBERS:
                    raise ValueError("nested ZIP member-count limit exceeded")
                name = info.filename
                parts = PurePosixPath(name)
                if (not name or "\\" in name or ":" in name or "\x00" in name
                        or parts.is_absolute() or ".." in parts.parts
                        or not self._safe_name(name, path.parent)):
                    raise ValueError(f"unsafe nested ZIP member: {name!r}")
                mode = info.external_attr >> 16
                if stat.S_IFMT(mode) == stat.S_IFLNK:
                    raise ValueError(f"nested ZIP symlink is not allowed: {name!r}")
                if info.flag_bits & 0x1:
                    raise ValueError(f"encrypted nested ZIP member: {name!r}")
                qualified = prefix + name
                if info.file_size < 0 or info.file_size > MAX_FINAL_MEMBER_BYTES:
                    raise ValueError(f"nested ZIP member exceeds size limit: {qualified!r}")
                if (name.lower().endswith((".cue", ".gdi", ".m3u"))
                        and info.file_size > MAX_DESCRIPTOR_BYTES):
                    raise ValueError(f"oversized nested ZIP descriptor: {qualified!r}")
                if (info.file_size and info.compress_size == 0) or (
                        info.compress_size and info.file_size > MAX_COMPRESSION_RATIO * info.compress_size):
                    raise ValueError(f"nested ZIP compression ratio limit exceeded: {qualified!r}")
                if qualified in self.members:
                    raise ValueError(f"duplicate nested ZIP member: {qualified!r}")
                if name.lower().endswith(".zip"):
                    if depth >= MAX_ZIP_LAYERS:
                        raise ValueError(f"nested ZIP depth limit exceeded: {qualified!r}")
                    if self._inner_count >= MAX_INNER_ARCHIVES:
                        raise ValueError("nested ZIP archive-count limit exceeded")
                    if info.file_size > MAX_INNER_BYTES or self._staged_bytes + info.file_size > MAX_STAGED_BYTES:
                        raise ValueError(f"nested ZIP staging size limit exceeded: {qualified!r}")
                    self._inner_count += 1
                    staged = Path(self._temp.name) / f"{self._inner_count}.zip"
                    with archive.open(info) as reader, staged.open("xb") as writer:
                        copied = 0
                        while chunk := reader.read(COPY_CHUNK):
                            copied += len(chunk)
                            if copied > info.file_size or copied > MAX_INNER_BYTES:
                                raise ValueError(f"nested ZIP member expanded beyond size declaration: {qualified!r}")
                            writer.write(chunk)
                    if copied != info.file_size:
                        raise ValueError(f"nested ZIP member size changed: {qualified!r}")
                    self._staged_bytes += copied
                    self._scan(staged, qualified + "/", depth + 1)
                else:
                    self._expanded_bytes += info.file_size
                    if self._expanded_bytes > MAX_EXPANDED_BYTES:
                        raise ValueError("nested ZIP expanded-file budget exceeded")
                    self.members[qualified] = ZipLeaf(path, name, info.file_size)

    def names(self) -> list[str]:
        """Return distinct, qualified ROM candidate names across ZIP layers."""
        return list(self.members)

    def member(self, qualified: str) -> ZipLeaf | None:
        """Look up an archive leaf without accepting unknown or aliased names."""
        return self.members.get(qualified)
