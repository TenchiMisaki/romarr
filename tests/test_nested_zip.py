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


def test_duplicate_inner_zip_container_names_fail_closed(tmp_path):
    """Two containers with the same name must not merge unrelated ROM sources."""
    download = tmp_path / "outer.zip"
    original_inner = zip_bytes({"Game.gb": b"game"})
    with zipfile.ZipFile(download, "w") as outer:
        outer.writestr("inner.zip", original_inner)
        with pytest.warns(UserWarning, match="Duplicate name"):
            outer.writestr("inner.zip", zip_bytes({"Other.gb": b"other"}))
    library = tmp_path / "library"

    result, = import_rom(download, resolve("gb"), library)
    assert not result.ok
    assert "duplicate nested ZIP member" in result.reason
    assert not library.exists()


@pytest.mark.parametrize("directory_download", [False, True])
def test_missing_nested_playlist_disc_never_publishes(tmp_path, directory_download):
    """A nested playlist lacking any referenced disc is not a valid game."""
    inner = zip_bytes({
        "Game.m3u": b"Disc One.chd\nDisc Two.chd\n",
        "Disc One.chd": b"one",
    })
    outer = zip_bytes({"inner.zip": inner})
    library = tmp_path / "library"
    if directory_download:
        download = tmp_path / "download"
        download.mkdir()
        (download / "outer.zip").write_bytes(outer)
        (download / "art.jpg").write_bytes(b"art")
    else:
        download = tmp_path / "outer.zip"
        download.write_bytes(outer)

    preview = preview_import(download, resolve("psx"), library)
    assert not preview["items"]
    result, = import_rom(download, resolve("psx"), library)
    assert not result.ok
    assert "no " in result.reason
    assert not library.exists()


@pytest.mark.parametrize("directory_download", [False, True])
def test_complete_nested_playlist_keeps_both_discs(tmp_path, directory_download):
    """A complete same-archive playlist remains selectable and playable."""
    inner = zip_bytes({
        "Game.m3u": b"Disc One.chd\nDisc Two.chd\n",
        "Disc One.chd": b"disc one",
        "Disc Two.chd": b"disc two",
    })
    outer = zip_bytes({"inner.zip": inner})
    library = tmp_path / "library"
    if directory_download:
        download = tmp_path / "download"
        download.mkdir()
        (download / "outer.zip").write_bytes(outer)
        (download / "art.jpg").write_bytes(b"art")
        primary = "outer.zip/inner.zip/Game.m3u"
    else:
        download = tmp_path / "outer.zip"
        download.write_bytes(outer)
        primary = "inner.zip/Game.m3u"

    preview = preview_import(download, resolve("psx"), library)
    assert [item["primary"] for item in preview["items"]] == [primary]
    result, = import_rom(download, resolve("psx"), library,
                         selected_primaries=[primary])
    assert result.ok, result.reason
    assert (result.destination / "Game.m3u").read_bytes() == b"Disc One.chd\nDisc Two.chd\n"
    assert (result.destination / "Disc One.chd").read_bytes() == b"disc one"
    assert (result.destination / "Disc Two.chd").read_bytes() == b"disc two"


def test_nested_zip_directory_entries_are_counted(tmp_path, monkeypatch):
    """Directories count toward the ZIP entry limit, not only files."""
    monkeypatch.setattr(nested_zip, "MAX_ZIP_MEMBERS", 3)
    inner = zip_bytes({"a/": b"", "b/": b"", "Game.gb": b"game"})
    download = tmp_path / "outer.zip"
    download.write_bytes(zip_bytes({"inner.zip": inner}))
    # The outer ZIP entry adds one; the inner ZIP adds three more.
    result, = import_rom(download, resolve("gb"), tmp_path / "library")
    assert not result.ok
    assert "member-count limit" in result.reason
    assert not (tmp_path / "library").exists()


def test_nested_zip_central_directory_byte_limit_before_parse(tmp_path, monkeypatch):
    """Reject oversized directory bytes before ZipFile builds member records."""
    monkeypatch.setattr(nested_zip, "MAX_CENTRAL_DIRECTORY_BYTES", 32)
    inner = zip_bytes({"Game.gb": b"game"})
    download = tmp_path / "outer.zip"
    download.write_bytes(zip_bytes({"inner.zip": inner}))
    result, = import_rom(download, resolve("gb"), tmp_path / "library")
    assert not result.ok
    assert "central-directory byte limit" in result.reason
    assert not (tmp_path / "library").exists()


def test_mame_archive_remains_the_playable_rom(tmp_path):
    """MAME's archive-is-the-ROM policy wins over nested ZIP discovery."""
    platform = resolve("mame")
    assert platform.archive_is_the_rom
    download = tmp_path / "arcade.zip"
    download.write_bytes(zip_bytes({"nested.zip": zip_bytes({"chip.bin": b"chip"})}))
    assert isinstance(_source_for(download, platform), _PathSource)
