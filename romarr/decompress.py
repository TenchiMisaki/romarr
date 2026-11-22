"""Batch decompression of a compressed ROM library.

The workflow issue #22 asked for: a library that was compressed (with
compressatorium or anything else) can be decompressed, every output validated
against the loaded DATs, and the compressed originals deleted -- but only the
ones that passed validation.

Division of labour:

  * **Compressatorium** does the extraction it has a tool for. It speaks
    CHD, RVZ/WIA/GCZ, Z3DS, NSZ, CSO/ZSO/DAX, WUX, NKit and single-cartridge
    7z/zip, each through the right tool (chdman, dolphin-tool, maxcso,
    nsz...). ROMarr does not reimplement any of that; it submits jobs to a
    running service, after asking it which of its tools are ready.
  * **ROMarr** extracts the archives the service has no mode for: RAR
    archives and split RAR sets (#224), and any .7z/.zip that is not one
    cartridge ROM (a zipped cue/bin, a multi-disc set). `decompress_local`
    does that with the importer's own archive readers, so those run even
    with no service configured.
  * **ROMarr** does the verdict. The DAT index lives here, and "is this the
    published dump" is answered by hash against that index -- the same
    question `dat.lookup` answers on every import. The service's own
    `/api/dat/match` is consulted as a second opinion for the formats whose
    hashes are embedded in the container (CHD, Dolphin images), where a
    plain file hash of the container cannot match a DAT of its contents.

Safety model, because the last step deletes files:

  * Originals are deleted only when `delete_originals=True` is passed
    explicitly AND every output of that original matched a DAT entry. For a
    split RAR set the original is every volume of the set.
  * An output that is `unknown` -- no DAT claims it -- keeps its original.
    No DAT does not mean bad file: homebrew, translations and anything an
    out-of-date DAT has not seen yet all land there, and deleting on
    unknown would destroy exactly the files a DAT cannot protect.
  * A `bad-dump` verdict keeps the original and fails the item loudly.
  * With no DATs loaded at all, nothing is ever deleted, however the flags
    are set. Verification is the gate; without it the gate stays shut.
  * Every step is logged: scan, submit, completion, per-file verdict, and
    each deletion. The log is the audit trail for a 500-file batch.

Dry run is a first-class mode: it scans and reports what would be processed,
and by which engine, without submitting a job or writing a file, so an
operator can see the blast radius before authorising a destructive one.
"""

from __future__ import annotations

import filecmp
import logging
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import decompress_local
from .compressatorium import (
    CANCELLED, COMPLETED, FAILED, TOOL_BY_MODE, UNAVAILABLE_REASON,
    CompressatoriumClient, CompressatoriumConfig, JobResult, mode_for,
    mode_for_file, romz_accepts,
)
from .dat import BAD_DUMP, UNKNOWN, VERIFIED, DatIndex, hash_file
from .library import rar_sets
from .selection import _cue_and_gdi_names

log = logging.getLogger(__name__)


# Extensions that count as "compressed" for the purposes of batch
# decompression. Kept in sync with compressatorium.mode_for: anything the
# client cannot name a mode for is not scanned, so the two lists agreeing is
# what makes the scan honest about what it can actually do. RAR is not here:
# RAR volumes are found by `library.rar_sets`, which knows all three volume
# namings, and they are always extracted locally.
COMPRESSED_EXTENSIONS: frozenset[str] = frozenset({
    # General-purpose archives
    ".7z", ".zip",
    # Compressed disc images (CHD, Dolphin RVZ/WIA/GCZ, CSO family)
    ".chd", ".rvz", ".wia", ".gcz", ".cso", ".zso", ".dax",
    # Compressed 3DS ROMs -- the z-prefixed forms only. `.cci`/`.cxi`/
    # `.cia` are the decompressed originals and must never be treated as
    # work to do.
    ".z3ds", ".zcxi", ".zcia", ".zcci", ".z3dsx",
    # Compressed Switch ROMs
    ".nsz", ".xcz",
    # Compressed Wii U images
    ".wux",
    # NKit-shrunk GameCube/Wii images (compound extensions -- matched with
    # endswith, never with Path.suffix)
    ".nkit.iso", ".nkit.gcz",
})

#: Engines an item can be planned to.
SERVICE = "compressatorium"
LOCAL = "local"

# How long to wait for the whole batch, and how often to poll. A CHD of a
# dual-layer DVD decompresses in minutes on spinning rust; a hundred of them
# queue behind one another on the service, so the batch budget is generous
# and the poll interval short enough that small jobs are not held up.
DEFAULT_JOB_TIMEOUT = 3 * 3600
DEFAULT_POLL_INTERVAL = 5


@dataclass(frozen=True)
class Work:
    """One unit the scan found: a file, or the first volume of a RAR set."""

    source: Path
    volumes: tuple[Path, ...] = ()


@dataclass
class DecompressItem:
    """One source file in the batch and what happened to it."""

    source: str
    status: str = "pending"
    # pending | skipped | submitted | decompressed | verified | failed |
    # deleted | kept
    job_id: str = ""
    mode: str = ""
    engine: str = ""             # compressatorium | local
    plan_note: str = ""          # why a file is extracted locally
    volumes: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    service_output_dir: str = field(default="", repr=False)
    dat_match: str = ""          # verified | bad-dump | unknown | ""
    dat_detail: str = ""
    error: str = ""
    deleted: bool = False
    #: (device, inode, size, mtime_ns, ctime_ns) of each original before work
    #: work started; deletion only removes a file that still matches.
    identities: dict = field(default_factory=dict, repr=False)
    #: Archive members that were not extracted; the original is then kept.
    skipped_members: list[str] = field(default_factory=list)


@dataclass
class DecompressReport:
    """Summary of a batch run."""

    scanned: int = 0
    submitted: int = 0
    extracted_locally: int = 0
    decompressed: int = 0
    verified: int = 0
    failed: int = 0
    deleted: int = 0
    kept: int = 0
    skipped: int = 0
    items: list[DecompressItem] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "submitted": self.submitted,
            "extracted_locally": self.extracted_locally,
            "decompressed": self.decompressed,
            "verified": self.verified,
            "failed": self.failed,
            "deleted": self.deleted,
            "kept": self.kept,
            "skipped": self.skipped,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "error": self.error,
            "items": [
                {
                    "source": it.source,
                    "status": it.status,
                    "job_id": it.job_id,
                    "mode": it.mode,
                    "engine": it.engine,
                    "plan_note": it.plan_note,
                    "volumes": it.volumes,
                    "output_files": it.output_files,
                    "dat_match": it.dat_match,
                    "dat_detail": it.dat_detail,
                    "error": it.error,
                    "deleted": it.deleted,
                }
                for it in self.items
            ],
        }


# ------------------------------------------------------------------ scan --

def _is_compressed_name(name: str, exts: frozenset[str]) -> bool:
    # Endswith rather than suffix: NKit images carry compound extensions
    # (`game.nkit.iso`) that `Path.suffix` reduces to `.iso`, and `.iso`
    # is NOT compressed -- matching on the suffix alone would either miss
    # every NKit file or, worse, pull in plain disc images. And the client
    # must actually know a mode for it, so the scan and the job submission
    # can never disagree.
    lowered = name.lower()
    return any(lowered.endswith(ext) for ext in exts) and bool(mode_for(lowered))


def scan_work(directory: str | Path, *,
              extensions: frozenset[str] | None = None) -> list[Work]:
    """Walk `directory` and return everything ROMarr knows how to decompress.

    Recursive. A RAR set is one unit, found through its first volume; its
    later volumes are never units of their own, because they can only be
    read through the first. Files with no decompression mode (`.iso`,
    `.n64`...) are not returned.
    """
    exts = extensions if extensions is not None else COMPRESSED_EXTENSIONS
    root = Path(directory)
    if not root.is_dir():
        log.warning("decompress: %s is not a directory", root)
        return []
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not _in_staging(p, root))
    sets, later = rar_sets(files)
    work: list[Work] = []
    for entry in files:
        if entry in later:
            continue
        if entry in sets:
            work.append(Work(entry, tuple(sets[entry])))
        elif _is_compressed_name(entry.name, exts):
            work.append(Work(entry))
    work.sort(key=lambda w: w.source.name.lower())
    return work


def _in_staging(path: Path, root: Path) -> bool:
    """Whether `path` sits in a local extraction's unfinished staging folder."""
    return any(part.startswith(decompress_local.STAGING_PREFIX)
               for part in path.relative_to(root).parts[:-1])


# -------------------------------------------------------------- planning --

def plan(work: Work) -> DecompressItem:
    """Which engine decompresses `work`, with which mode, and why.

    A local plan says why in `plan_note`, which a dry run shows.
    """
    item = DecompressItem(source=str(work.source),
                          volumes=[str(v) for v in work.volumes])
    if work.volumes:
        item.engine, item.mode = LOCAL, "extract"
        count = len(work.volumes)
        item.plan_note = (f"split RAR set of {count} volumes" if count > 1
                          else "RAR archive")
        item.plan_note += "; Compressatorium has no RAR mode"
        return item
    mode = mode_for_file(work.source)
    if mode == "romz_extract":
        members = decompress_local.archive_members(work.source)
        if members is not None and not romz_accepts(members):
            item.engine, item.mode = LOCAL, "extract"
            item.plan_note = (f"holds {len(members)} file(s), not one "
                              "cartridge ROM; romz_extract takes only that")
            return item
    item.engine, item.mode = SERVICE, mode
    return item


# ----------------------------------------------------------- verification --

def _output_files(output_path: str, published_files=()) -> list[str]:
    """Every regular file this job published.

    Directory outputs are enumerated within the isolated job directory. A
    file-shaped CUE/GDI output may include only its referenced tracks from that
    same directory; unrelated neighboring files are never part of the result.
    """
    if not output_path:
        return []
    out = Path(output_path)
    if out.is_symlink():
        return []
    published: set[Path] = set()
    if out.is_file():
        files = [out]
        job_root = out.parent.resolve()
        if isinstance(published_files, (list, tuple)):
            for value in published_files:
                if not isinstance(value, (str, Path)):
                    continue
                candidate = Path(value)
                if candidate.is_symlink() or not candidate.is_file():
                    return []
                try:
                    resolved = candidate.resolve(strict=True)
                    resolved.relative_to(job_root)
                except (OSError, ValueError):
                    continue
                published.add(resolved)
    elif out.is_dir():
        job_root = out.resolve()
        files = []
        for candidate in out.rglob("*"):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(job_root)
            except (OSError, ValueError):
                return []
            files.append(resolved)
    else:
        return []
    expanded = {p.resolve() for p in files}
    sheets = [p for p in files if p.suffix.casefold() in (".cue", ".gdi")]
    for sheet in sheets:
        try:
            names = _cue_and_gdi_names(sheet.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            return []
        if not names:
            return []
        root = sheet.parent.resolve()
        for name in names:
            relative = Path(name.replace("\\", "/"))
            if relative.is_absolute() or ":" in name:
                return []
            target = (root / relative).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                return []
            if not target.is_file():
                return []
            if target not in expanded:
                if target not in published:
                    return []
                files.append(target)
                expanded.add(target)
    return sorted(str(p) for p in expanded)

def _disc_outputs_complete(files: list[str]) -> bool:
    """Require every CUE/GDI track to be among this extraction's published files."""
    published = {Path(value).resolve() for value in files}
    for value in files:
        sheet = Path(value)
        if sheet.suffix.casefold() not in (".cue", ".gdi"):
            continue
        try:
            names = _cue_and_gdi_names(sheet.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            return False
        if not names:
            return False
        root = sheet.parent.resolve()
        for name in names:
            relative = Path(name.replace("\\", "/"))
            if relative.is_absolute() or ":" in name:
                return False
            target = (root / relative).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                return False
            if target not in published or not target.is_file():
                return False
    return True


def _second_opinion(fpath: str,
                    client: CompressatoriumClient | None) -> tuple[bool, str]:
    """Ask the service's DAT store about one file: (matched, detail)."""
    if client is None:
        return False, ""
    remote = client.match_file(fpath)
    if remote.matched:
        return True, f"{remote.game or 'matched'} ({remote.dat or 'server DAT'})"
    if remote.error:
        return False, f"Compressatorium could not match it: {remote.error}"
    return False, remote.detail


def _verify_outputs(files: list[str], dats: DatIndex,
                    client: CompressatoriumClient | None) -> tuple[str, str]:
    """Check every decompressed file against the DATs.

    Returns (status, detail) where status is "verified", "bad-dump" or
    "unknown". Verified means EVERY output matched a DAT entry. The service's
    own /api/dat/match, when a service is in use, is consulted as a second
    opinion for each file, which is what catches CHD and Dolphin outputs
    whose hashes are embedded in the container rather than being a plain
    file hash. A match the service could not work out stays unknown.
    """
    if not files:
        return UNKNOWN, "no output files produced"
    worst = VERIFIED
    details: list[str] = []
    for fpath in files:
        p = Path(fpath)
        if not p.is_file():
            worst = BAD_DUMP
            details.append(f"output missing: {fpath}")
            continue
        matched = False
        detail = ""
        file_bad = False
        # ROMarr's own index first -- it is local and free.
        try:
            hashes = hash_file(p)
            match = dats.lookup(**hashes)
            if match.status == VERIFIED:
                matched = True
                detail = f"{match.game} ({match.dat})"
            elif match.status == BAD_DUMP:
                file_bad = True
                detail = match.detail or "bad dump"
        except OSError as err:
            worst = BAD_DUMP
            details.append(f"could not hash {p.name}: {err}")
            continue
        if not matched:
            matched, remote_detail = _second_opinion(fpath, client)
            if matched:
                detail = remote_detail
            else:
                detail = detail or remote_detail
        if matched:
            details.append(f"{p.name}: verified {detail}".rstrip())
        elif file_bad:
            worst = BAD_DUMP
            details.append(f"{p.name}: {detail}")
        else:
            if worst == VERIFIED:
                worst = UNKNOWN
            details.append(f"{p.name}: {detail or 'not in any loaded DAT'}")
    # A bad-dump verdict outranks unknown: one corrupt output means the
    # extraction is suspect even if its siblings verified.
    return worst, "; ".join(details)


def _outputs_locally_verified(files: list[str], dats: DatIndex | None) -> bool:
    """Require fresh local DAT hashes before any destructive source cleanup.

    A service-side identification response can help explain an output, but
    does not expose enough evidence here to authorize deletion. Rehash every
    output at the deletion boundary so changed or missing files cannot inherit
    an earlier verification result.
    """
    if not files or dats is None or not dats.dats:
        return False
    for fpath in files:
        path = Path(fpath)
        try:
            if not path.is_file() or dats.lookup(**hash_file(path)).status != VERIFIED:
                return False
        except OSError:
            return False
    return True


# ----------------------------------------------------------------- engines --

def _skip(item: DecompressItem, report: DecompressReport, reason: str) -> None:
    item.status = "skipped"
    item.error = reason
    report.skipped += 1
    log.info("decompress: skipped %s: %s", Path(item.source).name, reason)


def _connect(url: str, api_key: str, service_items: list[DecompressItem],
             report: DecompressReport) -> CompressatoriumClient | None:
    """A client for the service, or None with every service item skipped.

    No URL or no answer used to end the whole batch. Now it ends only the
    work that needs the service: the RAR sets and multi-file archives ROMarr
    extracts itself still run.
    """
    if not url:
        if service_items:
            report.error = "no compressatorium URL configured"
        for item in service_items:
            _skip(item, report, "needs Compressatorium: set COMPRESSATORIUM_URL")
        return None
    client = CompressatoriumClient(CompressatoriumConfig(
        base_url=url, api_key=api_key))
    if not client.reachable():
        reason = f"compressatorium at {url} is not reachable"
        # `error` explains skipped work; with nothing for the service, the
        # local extractions are the whole run and it did not fail.
        if service_items:
            report.error = reason
        for item in service_items:
            _skip(item, report, reason)
        return None
    return client


def _gate_on_tools(client: CompressatoriumClient,
                   service_items: list[DecompressItem],
                   report: DecompressReport) -> list[DecompressItem]:
    """Skip the items whose tool the service reports unavailable."""
    available = client.available_tools()
    if available is None:
        return service_items
    ready = []
    for item in service_items:
        tool = TOOL_BY_MODE.get(item.mode, "")
        if tool and tool not in available:
            why = UNAVAILABLE_REASON.get(tool, "its prerequisites are missing")
            _skip(item, report, f"Compressatorium's {tool} tool is unavailable: {why}")
        else:
            ready.append(item)
    return ready


def _submit_jobs(client: CompressatoriumClient, items: list[DecompressItem],
                 output_dir: str | Path | None, report: DecompressReport) -> None:
    """Submit one job per item into an isolated output directory.

    Compressatorium reports one output_path. A unique directory lets ROMarr
    prove which adjacent tracks belong to that job without trusting unrelated
    files that happened to be beside the descriptor before it ran.
    """
    # Per-file jobs rather than /api/jobs/batch: the batch route takes ONE
    # mode for every file in the call, and a real library mixes CHD, RVZ,
    # 7z and NSZ in one directory. Grouping by mode to use the batch route
    # would buy one HTTP call per group and cost the per-file error
    # reporting that makes a failed batch diagnosable.
    for item in items:
        output_root = Path(output_dir) if output_dir else Path(item.source).parent
        try:
            output_root.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(
                prefix=f"{decompress_local.STAGING_PREFIX}service-",
                dir=output_root))
        except OSError as exc:
            item.status = "failed"
            item.error = f"could not prepare isolated service output directory: {exc}"
            report.failed += 1
            continue
        item.service_output_dir = str(staging)
        result: JobResult = client.submit_job(
            file_path=item.source,
            mode=item.mode,
            output_dir=str(staging),
            duplicate_action="skip",
        )
        if not result.job_id:
            item.status = "failed"
            item.error = result.error or "submission failed"
            report.failed += 1
            log.warning("decompress: submit failed for %s: %s",
                        Path(item.source).name, item.error)
            continue
        item.status = "submitted"
        item.job_id = result.job_id
        report.submitted += 1
        log.info("decompress: submitted %s as job %s (%s)",
                 Path(item.source).name, result.job_id, item.mode)


def _wait_for_jobs(client: CompressatoriumClient, items: list[DecompressItem],
                   job_timeout: int, poll_interval: int,
                   report: DecompressReport) -> None:
    """Wait for every submitted job and record each outcome."""
    job_ids = [it.job_id for it in items if it.job_id]
    final = client.wait_for_jobs(job_ids, timeout=job_timeout,
                                 poll_interval=poll_interval)
    for item in items:
        if item.status == "submitted":
            _record_job(item, final.get(item.job_id), job_timeout, report)


def _publish_service_outputs(item: DecompressItem) -> None:
    """Publish one isolated service result beside its source or in output_dir.

    Files are linked without clobbering when the filesystem permits it. A
    verified exclusive copy is the fallback for filesystems without hard links.
    Partial publication is rolled back only for destination inodes created here.
    """
    stage = Path(item.service_output_dir).resolve(strict=True)
    output_root = stage.parent
    planned: list[tuple[Path, Path]] = []
    for name in item.output_files:
        source = Path(name).resolve(strict=True)
        try:
            relative = source.relative_to(stage)
        except ValueError as exc:
            raise OSError(f"service output escaped its isolated directory: {name}") from exc
        destination = output_root / relative
        current = output_root
        for part in relative.parent.parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"publication parent is a symlink: {current}")
        try:
            destination.resolve().relative_to(output_root.resolve())
        except ValueError as exc:
            raise OSError(f"service output destination escaped output root: {destination}") from exc
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"output already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        current = output_root
        for part in relative.parent.parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"publication parent became a symlink: {current}")
        planned.append((source, destination))

    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for source, destination in planned:
            try:
                os.link(source, destination)
                stat = os.lstat(destination)
                created.append((destination, (stat.st_dev, stat.st_ino)))
            except OSError as link_error:
                if destination.exists() or destination.is_symlink():
                    raise FileExistsError(f"output already exists: {destination}") from link_error
                try:
                    with source.open("rb") as src, destination.open("xb") as dst:
                        stat = os.fstat(dst.fileno())
                        created.append((destination, (stat.st_dev, stat.st_ino)))
                        shutil.copyfileobj(src, dst)
                        dst.flush()
                        os.fsync(dst.fileno())
                    if not filecmp.cmp(source, destination, shallow=False):
                        raise OSError(f"published copy did not match {source.name}")
                except OSError:
                    raise
        item.output_files = [str(destination) for _, destination in planned]
    except OSError:
        for destination, identity in reversed(created):
            try:
                stat = os.lstat(destination)
                if (stat.st_dev, stat.st_ino) == identity:
                    destination.unlink()
            except OSError:
                pass
        raise

    try:
        shutil.rmtree(stage)
        item.service_output_dir = ""
    except OSError as exc:
        log.warning("decompress: published outputs but could not remove staging directory %s: %s",
                    stage, exc)


def _record_job(item: DecompressItem, status: JobResult | None,
                job_timeout: int, report: DecompressReport) -> None:
    if status is None:
        item.status = "failed"
        item.error = "job vanished from the service"
        report.failed += 1
    elif status.status == COMPLETED:
        stage = Path(item.service_output_dir).resolve() if item.service_output_dir else None
        output = Path(status.output_path)
        if stage is not None:
            if not output.is_absolute():
                output = stage / output
            try:
                resolved_output = output.resolve(strict=True)
                resolved_output.relative_to(stage)
            except (OSError, ValueError):
                item.status = "failed"
                item.error = "completed job output is missing or outside its isolated output directory"
                report.failed += 1
                log.warning("decompress: job %s returned an output outside its isolated directory",
                            item.job_id)
                return
            published_files = []
            for candidate in stage.rglob("*"):
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                try:
                    candidate.resolve(strict=True).relative_to(stage)
                except (OSError, ValueError):
                    continue
                published_files.append(str(candidate))
            item.output_files = _output_files(str(resolved_output), published_files)
        else:
            item.output_files = _output_files(status.output_path)
        if not item.output_files:
            item.status = "failed"
            item.error = "completed job produced no usable output files"
            report.failed += 1
            log.warning("decompress: job %s completed without usable outputs", item.job_id)
            return
        if stage is not None:
            try:
                _publish_service_outputs(item)
            except OSError as exc:
                item.status = "failed"
                item.error = f"could not publish complete service output set: {exc}"
                report.failed += 1
                log.warning("decompress: job %s: %s", item.job_id, item.error)
                return
        item.status = "decompressed"
        report.decompressed += 1
        log.info("decompress: job %s completed -> %d file(s)",
                 item.job_id, len(item.output_files))
    elif status.status == FAILED:
        item.status = "failed"
        item.error = status.error or "job failed"
        report.failed += 1
        log.warning("decompress: job %s failed: %s", item.job_id, item.error)
    else:
        # cancelled, or still running at the deadline
        item.status = "failed"
        item.error = (f"job ended as {status.status!r}"
                      if status.status == CANCELLED else
                      f"still {status.status!r} after {job_timeout}s")
        report.failed += 1
        log.warning("decompress: job %s: %s", item.job_id, item.error)


def _run_local(items: list[DecompressItem], output_dir: str | Path | None,
               report: DecompressReport) -> None:
    """Extract each item with ROMarr's own archive readers."""
    for item in items:
        source = Path(item.source)
        volumes = [Path(v) for v in item.volumes] or None
        root = Path(output_dir) if output_dir else source.parent
        try:
            result = decompress_local.extract_archive(source, volumes, root)
        except Exception as exc:  # one bad archive must not end the batch
            log.exception("decompress: unexpected error extracting %s", source.name)
            result = decompress_local.LocalExtraction(error=f"unexpected error: {exc}")
        if result.error:
            item.status = "failed"
            item.error = result.error
            report.failed += 1
            log.warning("decompress: could not extract %s: %s",
                        source.name, result.error)
            continue
        if not _disc_outputs_complete(result.output_files):
            item.status = "failed"
            item.error = "local extraction did not publish a complete CUE/GDI set"
            report.failed += 1
            log.warning("decompress: %s", item.error)
            continue
        item.status = "decompressed"
        item.output_files = result.output_files
        item.skipped_members = list(result.skipped_members)
        report.extracted_locally += 1
        report.decompressed += 1
        log.info("decompress: extracted %s locally -> %d file(s)",
                 source.name, len(result.output_files))


def _verify_all(items: list[DecompressItem], dats: DatIndex | None,
                client: CompressatoriumClient | None,
                report: DecompressReport) -> None:
    """Give every decompressed item its DAT verdict."""
    if dats is None or not dats.dats:
        for item in items:
            if item.status == "decompressed" and item.output_files:
                item.status = "kept"
                item.dat_match = UNKNOWN
                item.dat_detail = ("no DATs loaded -- verification skipped, "
                                   "originals kept")
                report.kept += 1
                log.warning("decompress: %s decompressed but no DATs loaded "
                            "for verification", Path(item.source).name)
        return
    for item in items:
        if item.status != "decompressed":
            continue
        status, detail = _verify_outputs(item.output_files, dats, client)
        item.dat_match = status
        item.dat_detail = detail
        name = Path(item.source).name
        if status == VERIFIED:
            item.status = "verified"
            report.verified += 1
            log.info("decompress: %s verified against DAT", name)
        elif status == BAD_DUMP:
            item.status = "failed"
            item.error = f"DAT verification: {detail}"
            report.failed += 1
            log.warning("decompress: %s is a BAD DUMP: %s", name, detail)
        else:
            # Unknown: extracted fine, but no DAT claims it. Kept, never
            # deleted -- see the module docstring for why.
            item.status = "kept"
            report.kept += 1
            log.info("decompress: %s extracted but unknown to the DATs; "
                     "original kept", name)


def _identity(path: Path):
    try:
        st = os.lstat(path)
    except OSError:
        return None
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def _originals(item: DecompressItem) -> list[Path]:
    """An item's original files, first volume last.

    A RAR set is found by its first volume, so it goes last: a deletion that
    stops part-way still leaves a set the next batch can find.
    """
    paths = [Path(v) for v in item.volumes] or [Path(item.source)]
    first = Path(item.source)
    return [p for p in paths if p != first] + [p for p in paths if p == first]


def _record_identities(items: list[DecompressItem]) -> None:
    for item in items:
        item.identities = {str(p): _identity(p) for p in _originals(item)}


def _restore_aside(aside: Path, original: Path) -> bool:
    """Restore a renamed original without clobbering a concurrent file."""
    try:
        os.link(aside, original)
    except OSError as err:
        # On Windows, hard links can be denied even when same-volume rename is
        # permitted. os.rename refuses an existing destination on that host,
        # preserving the no-clobber rollback guarantee.
        if os.name == "nt" and getattr(err, "winerror", None) == 5:
            try:
                os.rename(aside, original)
                return True
            except OSError:
                return False
        return False
    try:
        os.unlink(aside)
    except OSError:
        # Both paths still name the same original bytes. The caller reports
        # that the aside remains so recovery is visible.
        return False
    return True


def _delete_if_unchanged(path: Path, expected) -> str:
    """Delete `path` only if it is still the file that was extracted.

    The file is first renamed aside -- atomic, so a replacement arriving after
    that point gets the name back and is never touched -- and the renamed file
    is the one checked and removed. Returns "" when removed, "missing" when it
    is already gone, otherwise why it was kept.
    """
    if not expected:
        return f"{path.name}: not seen before extraction, kept"
    if _identity(path) != list(expected):
        return f"{path.name}: changed since it was extracted, kept"
    aside = path.with_name(f".{path.name}.romarr-deleting-{uuid.uuid4().hex[:8]}")
    try:
        os.rename(path, aside)
    except FileNotFoundError:
        return "missing"
    except OSError as err:
        return f"{path.name}: {err}"
    # rename changes ctime on POSIX. The complete snapshot was checked just
    # before the atomic move; after it, require the same inode and content-size
    # metadata while allowing the rename's ctime update.
    moved = _identity(aside)
    if moved is None or moved[:4] != list(expected)[:4]:
        if _restore_aside(aside, path):
            return f"{path.name}: changed since it was extracted, kept"
        return f"{path.name}: changed since it was extracted, kept as {aside.name}"
    try:
        os.unlink(aside)
    except OSError as err:
        _restore_aside(aside, path)
        return f"{path.name}: {err}"
    return ""


def _backup_rar_set(paths: list[Path], identities: dict[str, Any]) -> tuple[Path, dict[Path, Path]]:
    """Make verified rollback copies before deleting any split-set volume."""
    parents = {path.parent.resolve() for path in paths}
    if len(parents) != 1:
        raise OSError("RAR volumes are not in one directory")
    parent = next(iter(parents))
    backup_dir = Path(tempfile.mkdtemp(prefix=".romarr-rar-rollback-", dir=parent))
    backups: dict[Path, Path] = {}
    try:
        for path in paths:
            expected = identities.get(str(path))
            if not expected or _identity(path) != list(expected):
                raise OSError(f"{path.name} changed since it was extracted")
            backup = backup_dir / path.name
            # A hard link increments the source inode's link count and changes
            # ctime on POSIX, invalidating the recorded identity. Independent
            # copies keep the source metadata stable for the cleanup check.
            shutil.copyfile(path, backup)
            if (hash_file(path) != hash_file(backup)
                    or _identity(path) != list(expected)):
                raise OSError(f"could not verify rollback copy of {path.name}")
            backups[path] = backup
        return backup_dir, backups
    except BaseException:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise


def _restore_backup(backup: Path, original: Path) -> bool:
    """Restore a deleted volume without replacing a concurrent file."""
    try:
        os.link(backup, original)
    except OSError as err:
        if os.name == "nt" and getattr(err, "winerror", None) == 5:
            try:
                os.rename(backup, original)
                return True
            except OSError:
                return False
        try:
            # O_EXCL is the portable no-clobber fallback when hard links are
            # unavailable. A failed partial copy is removed only if we created it.
            created_identity = None
            with backup.open("rb") as source, original.open("xb") as target:
                before = os.fstat(target.fileno())
                created_identity = (before.st_dev, before.st_ino)
                shutil.copyfileobj(source, target)
                target.flush()
                os.fsync(target.fileno())
            return True
        except OSError:
            if created_identity is not None:
                try:
                    current = os.lstat(original)
                    if (current.st_dev, current.st_ino) == created_identity:
                        original.unlink()
                except OSError:
                    pass
            return False
    try:
        backup.unlink()
    except OSError:
        return False
    return True


def _delete_originals(items: list[DecompressItem],
                      report: DecompressReport,
                      dats: DatIndex | None) -> None:
    """Delete each verified item's original: its file, or every RAR volume."""
    for item in items:
        if item.status != "verified" or item.dat_match != VERIFIED:
            continue
        if not _outputs_locally_verified(item.output_files, dats):
            item.status = "kept"
            item.dat_match = UNKNOWN
            item.dat_detail = (
                (item.dat_detail + "; ") if item.dat_detail else ""
            ) + "outputs lack a fresh local DAT hash match; original kept"
            report.verified -= 1
            report.kept += 1
            log.warning("decompress: kept original %s because outputs were "
                        "not freshly verified against local DATs",
                        Path(item.source).name)
            continue
        if item.skipped_members:
            item.status = "kept"
            item.error = ("original kept: some members could not be extracted safely: "
                          + ", ".join(item.skipped_members[:5]))
            report.verified -= 1
            report.kept += 1
            log.warning("decompress: kept %s: %s", Path(item.source).name, item.error)
            continue
        failures = []
        removed = 0
        removed_paths: list[Path] = []
        originals = _originals(item)
        backup_dir = None
        backups = {}
        if len(originals) > 1:
            try:
                backup_dir, backups = _backup_rar_set(originals, item.identities)
            except OSError as err:
                item.status = "kept"
                item.error = f"split RAR set kept; rollback copy failed: {err}"
                report.verified -= 1
                report.kept += 1
                log.warning("decompress: %s", item.error)
                continue
            if not _outputs_locally_verified(item.output_files, dats):
                shutil.rmtree(backup_dir, ignore_errors=True)
                item.status = "kept"
                item.dat_match = UNKNOWN
                item.error = "split RAR outputs changed during backup; originals kept"
                report.verified -= 1
                report.kept += 1
                log.warning("decompress: %s", item.error)
                continue
        for path in originals:
            outcome = _delete_if_unchanged(path, item.identities.get(str(path)))
            if outcome == "missing":
                failures.append(f"{path.name}: changed or disappeared before cleanup")
                break
            if outcome:
                failures.append(outcome)
                log.warning("decompress: kept %s", outcome)
                # The rest of the set stays together, first volume included.
                break
            removed += 1
            removed_paths.append(path)
        if failures and backups:
            restore_failures = []
            for path in removed_paths:
                if not _restore_backup(backups[path], path):
                    restore_failures.append(str(backups[path]))
            if restore_failures:
                item.error = ("could not delete original set; recovery copies "
                              "remain at " + ", ".join(restore_failures))
            else:
                item.error = "could not delete original set; all removed volumes restored"
            if not restore_failures:
                shutil.rmtree(backup_dir, ignore_errors=True)
            item.status = "kept"
            report.verified -= 1
            report.kept += 1
            continue
        if backup_dir is not None:
            try:
                shutil.rmtree(backup_dir)
            except OSError as err:
                item.error = f"originals deleted; rollback copies remain at {backup_dir}: {err}"
        if failures:
            item.error = "could not delete original: " + "; ".join(failures)
        if removed and not failures:
            item.deleted = True
            item.status = "deleted"
            report.deleted += 1
            log.info("decompress: deleted original %s%s (verified: %s)",
                     Path(item.source).name,
                     f" and its {removed - 1} other volume(s)" if removed > 1 else "",
                     item.dat_detail)


# ---------------------------------------------------------------- the batch --

def run_batch(
    directory: str | Path,
    *,
    compressatorium_url: str = "",
    compressatorium_api_key: str = "",
    dats: DatIndex | None = None,
    delete_originals: bool = False,
    output_dir: str | Path | None = None,
    job_timeout: int = DEFAULT_JOB_TIMEOUT,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    dry_run: bool = False,
) -> DecompressReport:
    """Decompress every compressed file in `directory`.

    Parameters
    ----------
    directory
        Root to scan for compressed files.
    compressatorium_url
        Base URL of the service. Without it, only the work ROMarr extracts
        itself (RAR sets, multi-file archives) runs; the rest is skipped and
        `error` says why.
    compressatorium_api_key
        Bearer token, when the service has auth enabled.
    dats
        ROMarr's loaded DAT index. With None (or an empty index) nothing is
        ever deleted, whatever delete_originals says -- verification is the
        gate and without DATs the gate stays shut.
    delete_originals
        Delete each compressed original after its outputs verify. False by
        default; the API requires an explicit true in the request body.
    output_dir
        Where outputs are written. Default: alongside each source, which is
        what the service does when the field is omitted.
    job_timeout
        Seconds to wait for the whole batch to reach a terminal state.
    poll_interval
        Seconds between status polls.
    dry_run
        Scan and report without submitting or writing anything.
    """
    report = DecompressReport()
    t0 = time.monotonic()

    work = scan_work(directory)
    report.scanned = len(work)
    log.info("decompress: scanned %s, found %d compressed file(s)",
             directory, len(work))
    items = [plan(w) for w in work]
    report.items = items

    if not items:
        report.elapsed_seconds = time.monotonic() - t0
        return report

    if dry_run:
        for item in items:
            item.status = "skipped"
            if item.engine == LOCAL:
                item.dat_detail = f"dry run -- would extract locally ({item.plan_note})"
            else:
                item.dat_detail = f"dry run -- would run {item.mode} on Compressatorium"
            report.skipped += 1
        report.elapsed_seconds = time.monotonic() - t0
        log.info("decompress: dry run, %d file(s) would be processed", len(items))
        return report

    # The deletion gate. Decided once, here, rather than at each deletion
    # site: deleting an original is only ever justified by a DAT match, and
    # with no index loaded there is nothing that could produce one.
    can_delete = bool(delete_originals) and dats is not None and bool(dats.dats)
    if delete_originals and not can_delete:
        log.warning("decompress: delete_originals requested but no DATs are "
                    "loaded -- originals will be KEPT regardless of outcome")

    if can_delete:
        # Before anything reads them: deletion later removes only these files.
        _record_identities(items)
    service_items = [it for it in items if it.engine == SERVICE]
    local_items = [it for it in items if it.engine == LOCAL]
    client = _connect(compressatorium_url, compressatorium_api_key,
                      service_items, report)
    ready: list[DecompressItem] = []
    if client is not None and service_items:
        ready = _gate_on_tools(client, service_items, report)
        _submit_jobs(client, ready, output_dir, report)
    # The service works through its queue while ROMarr extracts its own share.
    _run_local(local_items, output_dir, report)
    if ready:
        _wait_for_jobs(client, ready, job_timeout, poll_interval, report)

    _verify_all(items, dats, client, report)

    if can_delete:
        _delete_originals(items, report, dats)
    elif any(it.status == "verified" for it in items):
        log.info("decompress: %d file(s) verified but originals kept "
                 "(deletion not authorised)",
                 sum(1 for it in items if it.status == "verified"))

    report.elapsed_seconds = time.monotonic() - t0
    log.info("decompress: batch complete -- %d scanned, %d submitted, "
             "%d extracted locally, %d verified, %d kept, %d failed, "
             "%d deleted in %.1fs",
             report.scanned, report.submitted, report.extracted_locally,
             report.verified, report.kept, report.failed, report.deleted,
             report.elapsed_seconds)
    return report
