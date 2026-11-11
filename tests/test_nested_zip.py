"""Regression coverage for bounded ZIP-inside-ZIP import and review."""

import io
import stat
import zipfile

import pytest

from romarr import nested_zip
from romarr.import_intent import preview_import
from romarr.library import _PathSource, _source_for, import_rom
from romarr.platforms import resolve


def zip_bytes(members):
    """Build an in-memory ZIP so tests never need downloaded game data."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def test_nested_zip_preview_and_import_preserve_original(tmp_path):
    """Import an inner ZIP's ROM without altering the seeded outer archive."""
    original = zip_bytes({"inside.zip": zip_bytes({"Game.gb": b"game bytes"})})
    download = tmp_path / "download.zip"
    download.write_bytes(original)
    library = tmp_path / "library"

    preview = preview_import(download, resolve("gb"), library)
    assert not preview["requires_review"]
    assert preview["items"][0]["primary"] == "inside.zip/Game.gb"
    assert preview["items"][0]["bytes"] == len(b"game bytes")

    result, = import_rom(download, resolve("gb"), library,
                         selected_primaries=["inside.zip/Game.gb"])
    assert result.ok, result.reason
    assert result.destination.read_bytes() == b"game bytes"
    assert download.read_bytes() == original
    assert result.import_method == "extracted"


def test_nested_zip_disc_in_directory_preserves_tracks_and_art(tmp_path):
    """Retain a disc's CUE/BIN companions when ZIPs are nested in a folder."""
    download = tmp_path / "download"
    download.mkdir()
    outer = download / "outer.zip"
    original = zip_bytes({"inner.zip": zip_bytes({
        "Game.cue": b'FILE "track.bin" BINARY\n',
        "track.bin": b"track payload",
    })})
    outer.write_bytes(original)
    (download / "art.jpg").write_bytes(b"art")

    primary = "outer.zip/inner.zip/Game.cue"
    preview = preview_import(download, resolve("dc"), tmp_path / "library")
    assert [item["primary"] for item in preview["items"]] == [primary]
    result, = import_rom(download, resolve("dc"), tmp_path / "library",
                         selected_primaries=[primary])
    assert result.ok, result.reason
    assert (result.destination / "Game.cue").read_bytes() == b'FILE "track.bin" BINARY\n'
    assert (result.destination / "track.bin").read_bytes() == b"track payload"
    assert outer.read_bytes() == original
    assert (download / "art.jpg").read_bytes() == b"art"


def test_two_inner_zip_sets_remain_separate_under_review(tmp_path):
    """Selecting one disc must not pick the other ZIP's identically named track."""
    download = tmp_path / "outer.zip"
    download.write_bytes(zip_bytes({
        "A.zip": zip_bytes({"Game.cue": b'FILE "track.bin" BINARY\n', "track.bin": b"a"}),
        "B.zip": zip_bytes({"Game.cue": b'FILE "track.bin" BINARY\n', "track.bin": b"b"}),
    }))
    preview = preview_import(download, resolve("dc"), tmp_path / "library")
    assert preview["requires_review"]
    assert {item["primary"] for item in preview["items"]} == {
        "A.zip/Game.cue", "B.zip/Game.cue"}
    result, = import_rom(download, resolve("dc"), tmp_path / "library",
                         selected_primaries=["B.zip/Game.cue"])
    assert result.ok, result.reason
    assert (result.destination / "track.bin").read_bytes() == b"b"


@pytest.mark.parametrize("violation", ["depth", "traversal", "corruption", "count", "size", "symlink"])
def test_nested_zip_fails_before_library_publication(tmp_path, monkeypatch, violation):
    """Reject unsafe or excessive archive trees without publishing any ROM."""
    inner = zip_bytes({"Game.gb": b"good"})
    if violation == "depth":
        for number in range(nested_zip.MAX_ZIP_LAYERS):
            inner = zip_bytes({f"layer{number}.zip": inner})
    elif violation == "traversal":
        inner = zip_bytes({"../Game.gb": b"bad"})
    elif violation == "corruption":
        inner = b"invalid zip content"
    elif violation == "count":
        monkeypatch.setattr(nested_zip, "MAX_ZIP_MEMBERS", 1)
    elif violation == "size":
        monkeypatch.setattr(nested_zip, "MAX_INNER_BYTES", 1)
    elif violation == "symlink":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("Game.gb")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b"bad-link")
        inner = buffer.getvalue()
    if violation != "depth":
        inner = zip_bytes({"inner.zip": inner})
    download = tmp_path / "outer.zip"
    download.write_bytes(inner)
    library = tmp_path / "library"

    result, = import_rom(download, resolve("gb"), library)
    assert not result.ok
    assert "source inspection failed" in result.reason
    assert not library.exists()


def test_mame_archive_remains_the_playable_rom(tmp_path):
    """MAME's archive-is-the-ROM policy wins over nested ZIP discovery."""
    platform = resolve("mame")
    assert platform.archive_is_the_rom
    download = tmp_path / "arcade.zip"
    download.write_bytes(zip_bytes({"nested.zip": zip_bytes({"chip.bin": b"chip"})}))
    assert isinstance(_source_for(download, platform), _PathSource)
