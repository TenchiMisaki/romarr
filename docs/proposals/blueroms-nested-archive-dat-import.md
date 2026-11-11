> **ROMarr ZIP-import backlog — DRAFT, DO NOT MERGE.**
> This PR contains the complete investigation of multiple ZIP files in one download, ZIP-inside-ZIP support, DAT-verified game selection, and safe import. Read the full content below to resume the investigation. The same content is versioned in [the companion Markdown file](https://github.com/TenchiMisaki/romarr/blob/notes/blueroms-multi-archive-dat-import/docs/proposals/blueroms-nested-archive-dat-import.md).
> **No ZIP-import functionality has been implemented or tested by this PR.**


> **Latest related upstream work (Nov 10, 2026):** [PR #146](https://github.com/BlizzHacker/romarr/pull/146) proposes support for archives found *in download folders*, addressing the original sibling-ZIP discovery case. Literal ZIP-inside-ZIP traversal and request-aware game identification remain separate, unverified backlog work; see §10. This backlog PR is still draft/documentation-only.

---

# Future investigation: BlueRoms multi-archive discovery and DAT-verified import

> **Status:** Deferred investigation and feature-design handoff — **not an upstream issue, confirmed current bug, implemented fix, or tested enhancement**.
>
> **Purpose:** Preserve the full technical investigation of ROMarr ZIP import behavior for a future assistant/developer to resume without reconstructing the original discussions. This is a personal-fork working note, **not a maintainer-facing submission**. The fork is public: do not append credentials, private paths, download URLs, user-specific infrastructure data, or copyrighted ROM payloads.
>
> **Investigation scope:** Multiple sibling ZIP archives and ZIP-inside-ZIP inputs, selecting the requested ROM, DAT-verifying actual bytes, and safely importing the correct game. No unrelated process or application changes are proposed.

**Prepared:** 2026-11-09  
**Personal fork:** [TenchiMisaki/romarr](https://github.com/TenchiMisaki/romarr)  
**Official project:** [BlizzHacker/romarr](https://github.com/BlizzHacker/romarr)  
**Reference official `main` inspected:** `9bf31ffcef3913798252e4c678f12f1544b07a2a` (2026-11-09 read-only source check; verify freshness on resumption)  
**Fork `main` used for this notes branch:** `041a367cedeb1c4b66365a9daea6a095cc753d55`  
**Intended test source:** BlueRoms (real-world example) plus synthetic fixtures  
**No tests or ROMarr file modifications were performed to create this note.**

## 1. Goal and requested behavior

Automatically discover eligible ROM files inside:

1. A completed download folder containing **multiple separate ZIP archives**.
2. An archive containing **another archive** (literal ZIP-within-ZIP).
3. Supported additional archive formats or directory nesting where existing ROMarr archive tooling supports them.

After discovery, **verify the actual ROM bytes** using ROMarr's existing platform rules and configured DAT catalogs (e.g. No-Intro/Redump). When one appropriate, confidently identified game matches the original request and configured import policy, import it automatically without routine manual selection or extraction. If identity, contents, or policy are ambiguous, **retain the download and require review**.

This is not a request for a new, independent DAT verifier. It should reuse the existing import, selection, DAT and intent machinery.

### Key distinction

- A ROM may be **verified by a DAT** yet still be **the wrong game** for the request; these are two separate checks.
- A file with **no matching DAT** is not automatically corrupt; preserve the existing **UNKNOWN** classification.
- Multiple ZIP files **beside each other** are *not* the same structural case as a ZIP nested inside another ZIP. Test both independently.

## 2. Historical BlueRoms evidence (not new verification)

The October 29–30, 2026 investigation involved **four Sonic ZIP archives** in completed download content, each containing Sega Genesis/Mega Drive `.md` ROMs. Direct ZIP inspection indicated readable members and successful ZIP integrity/CRC checks for the tested archives. The ROMarr completed-directory import path did not recognize the expected Genesis ROMs.

**Supported historical hypothesis:** ROMarr was given a *directory with multiple archives* and enumerated the ZIPs themselves rather than their game members. This is consistent with inspected importer source, but needs fresh reproduction on a pinned current revision.

**Not established:** Those BlueRoms examples contained a literal outer ZIP enclosing an inner ZIP. The ZIP-within-ZIP path is a **proposed additional test and feature**, not a claim about the previously captured BlueRoms archive layout.

**Adjacent but distinct issue:** An earlier Castlevania: Bloodlines verification case produced an unrelated DAT/bad-dump association (a different title with size-based matching). Preserve this as a separate verification/identity edge case, not proof that nested-archive handling would fix it.

Do not present old observed downloads as present/current, current torrent ownership or client path data, or a current production failure until independently checked.

## 3. Source observations and exact review anchors

Reviewed official `main` at `9bf31ffcef3913798252e4c678f12f1544b07a2a`. The following is **source inspection only**, not execution:

- [`romarr/library.py`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/library.py) — `_source_for(download, platform)` unwraps a directory's archive only when there is **exactly one immediate, non-hidden file** and that file is an archive. With several archive files it falls through to `_PathSource`, whose `names()` recursively lists files on disk but does not open every ZIP as an archive. Direct ZIP inputs use `_ZipSource`; supported other archive inputs can use `_BsdtarSource`, subject to installed tooling.
- In the same file, `import_rom` calls `pick_all_rom_sets` and `verify_set`. `verify_set` hashes each selected ROM-set member, checks configured DATs, requires verification of all members to classify a set as VERIFIED, and returns UNKNOWN when DATs are absent or hashing cannot establish a result. Check the actual status/priority logic again before implementation.
- [`romarr/selection.py`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/selection.py) — existing ROM-set selection and companion grouping.
- [`romarr/platforms.py`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/platforms.py) — `archive_is_the_rom` platform behavior must remain intact (e.g. arcade ROM sets and DOSBox).
- [`romarr/selective_import.py`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/selective_import.py) — preserve exact selected download-client file identity, progress/priority and containment; do not replace this with indiscriminate collection-root scanning.
- [`romarr/import_intent.py`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/import_intent.py) and [`docs/import-selection.md`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/docs/import-selection.md) — preserve explicit bundle choices, review tokens, retries and collection import behavior.

**Important:** Some parts of source are only named as future inspection anchors. This note is **not a full current-codebase audit**, and no automated regression result or live import behavior has been established for the proposed feature.

## 4. Avoid duplicating already addressed upstream work

Relevant upstream work checked on 2026-11-09:

- [Issue #115](https://github.com/BlizzHacker/romarr/issues/115) — collection selected-archive handling; **closed 2026-11-03**.
- [Issue #123](https://github.com/BlizzHacker/romarr/issues/123) — explicitly selected ZIP nested under a *collection directory* / `content_path`; **closed 2026-11-06**. This is a directory hierarchy issue and **not evidence of ZIP-inside-ZIP support**.
- [Issue #126](https://github.com/BlizzHacker/romarr/issues/126) — manual bundle preview and selection; **closed 2026-11-06**.
- [PR #127](https://github.com/BlizzHacker/romarr/pull/127) — related import-selection and selected-archive improvements.

Before any public report or source fix, recheck **current upstream main, existing issues/PRs, release behavior and actual installed revision**. A closed issue, merged PR, released build and installed/verified user behavior are distinct.

## 5. Proposed automatic decision flow

1. Start only from a **completed and identified download job** (do not ingest partial/unselected torrent members).
2. Resolve the correct selected source boundary and mapped path; preserve original download identity and its import intent.
3. Enumerate regular files and supported archive members using safe, **bounded** traversal. Allow multiple sibling archives and nested archives to an explicit depth limit; do not recurse blindly.
4. Where a platform treats an archive as the playable ROM, **keep it intact**. Otherwise inspect eligible ROM members or complete ROM sets, including essential companions.
5. Reuse existing platform candidate selection and **DAT hash verification**. Do not treat filenames, matching file sizes, or an archive CRC pass as proof of the expected game.
6. Independently compare identified DAT/platform/title/release context with the **requested game**. A verified ROM for another title is not automatic fulfillment.
7. Apply existing `require_verified`, rename/layout, bundle-selection, duplicate/collision and request/collection policies. **Auto-import only an unambiguous, policy-accepted result**.
8. For multiple legitimate games, conflicting matches, unknown data, changed source identity or unclear requests, preserve source and present the existing review workflow rather than guessing.
9. Record sufficient sanitized reason/status to distinguish **not found**, **unknown verification**, **true failed verification**, **ambiguous requested title**, **unsupported format**, **incomplete source**, **safety limit**, and **import failure**.
10. Preserve original downloads and seeding, do not overwrite existing library files, and avoid duplicates on retries/restarts.

### Safety boundaries

- Enforce a maximum archive nesting depth, expanded bytes, number of files, processing duration and reasonable memory/CPU usage. Prevent decompression bombs and unbounded recursion.
- Reject path traversal, unsafe member names, symlink escapes and archive entries that violate source/staging containment.
- Use safe temporary staging or streaming for nested archives, clean only owned temporary data after verification, and keep failure/recovery evidence.
- Avoid loading large disc images into memory; preserve existing streamed hashing where applicable.
- Retain grouped CUE/BIN, GDI, multidisc and platform-specific ROM-set behavior.
- Prevent an import of a wrong-title DAT match, silently ignored ambiguous extras, or an unselected member of a collection.
- No automatic data deletion or torrent-priority changes just because an archive member was excluded.

## 6. Planned reproduction and regression matrix

All cases are **NOT TESTED for this feature** until a future session collects actual evidence.

| Case | Fixture / BlueRoms layout | Expected outcome |
|---|---|---|
| A | One completed folder → one ZIP → one Genesis `.md` | Existing automatic workflow remains functional |
| B | One completed folder → two or more sibling ZIPs → Genesis ROMs | Discover eligible inner ROMs; respect requested game/collection intent |
| C | Outer ZIP → inner ZIP → Genesis `.md` | Verify actual ROM; auto-import uniquely accepted target |
| D | Additional nested archive levels | Stop at documented bound; clear review/safety reason |
| E | Multiple valid games across inner ZIPs | Respect explicit multi-game intent; never fulfill one request with arbitrary game |
| F | Exact platform/DAT game match | Verified result and correct requested-title decision |
| G | Valid DAT checksum for the **wrong** title | Do not silently import/fulfill request |
| H | DAT absent; recognized extension | UNKNOWN, not fabricated BAD_DUMP; follow configured verification/review policy |
| I | Wrong checksum/size or corrupt ZIP | Distinct classification; no unchecked automatic import |
| J | Arcade `archive_is_the_rom`, DOSBox, other special platforms | Archive stays playable/intact |
| K | Multi-track disc/CUE/BIN, GDI and multidisc | All required members retained and verified as a group |
| L | Incomplete/partial torrent member; selected archive among unrelated files | Respect completion and exact selected source identity |
| M | Duplicate destination, repeated sweep/restart, changed source | No overwrite, duplicate import, or stale intent reuse |
| N | Traversal, unsafe symlink, decompression-bomb and resource-limit fixture | Fail closed without unsafe writes |

**Suggested evaluation sequence:** (1) Pin exact current upstream revision, (2) reproduce historical sibling-ZIP behavior with synthetic files on unmodified source, (3) reproduce literal nested-ZIP behavior separately, (4) collect sanitized BlueRoms layout and actual import logs under approved testing, (5) implement the smallest source change in an isolated branch/worktree, (6) rerun focused regressions, review the final code, and validate actual ZIP import behavior only in an approved isolated test environment with verified rollback.

## 7. Evidence to collect when this is resumed

- Actual ROMarr production/preview versions or source revisions **as verified at that future date**, not inferred from a tag or old documentation.
- Download-client type/version and source metadata: completion, selected files, logical `content_path` and mapped source (sanitize private filesystem details).
- Exact archive nesting tree and safe member metadata, platform, extension and benign synthetic fixture bytes/hashes. No ROM payloads or copyrighted download links in this public note.
- DAT catalog name/version and expected title, actual status, checksum verdict, identity resolution and original request.
- Full result statuses/reasons, affected paths sanitized, whether any media/destination was actually changed, and exact test/review outcomes.
- Source revision/commit, tests and fixtures, existing behavior comparison, regressions and CodeRabbit finding dispositions.
- If a ZIP-import test build is deployed in an isolated preview, capture the exact revision, backup verification, rollback readiness, results, and final restored or retained state.

**Don't conflate** ZIP CRC integrity, successful DAT lookup, correct requested-game identity and actual playable library import: each is a different acceptance check.

## 8. Future action and authorization

When the owner asks to resume:

1. Read this full ZIP-import investigation, its pinned ROMarr source links, related upstream issues/PRs, test matrix, and any newer evidence. Reconfirm the actual current repository and test-environment revisions before reusing prior findings.
2. Check whether upstream now supports sibling archives, nested ZIPs and request-aware DAT validation. Determine the actual remaining gap; revise scope if upstream implemented it.
3. Produce a read-only reproduction plan using synthetic ZIP files before changing ROMarr code, completed download content, library files, or running services.
4. Use BlueRoms **as the real-world example** and synthetic archives for safe reproducible tests. Do not assume BlueRoms must still serve the same archive layout.
5. Develop only after separate owner approval on an isolated branch, preserving the active contributor PR, fork `main`, original downloads, library data, and production ROMarr. Never change a live preview without verifying the exact test target, independent backup, functioning rollback plan, and the required five-minute rollback safeguard; do not assume this safeguard has already been installed or tested.
6. Only after successful, documented reproduction and fix validation decide whether to prepare a **separate upstream issue or PR**. This internal document is not that publication.

**Current disposition:** Deferred / future research. **Code modification: NONE. Runtime testing: NONE. Upstream issue/PR created for this proposal: NONE.**

## 9. November 9, 2026 PST — Related upstream 7z/RAR extraction issue #144 (watch)

**Related issue to follow:** [BlizzHacker/romarr #144 — 7z/RAR member extraction fails when filenames contain glob metacharacters](https://github.com/BlizzHacker/romarr/issues/144). **Status when checked November 9 PST: OPEN.** This is a separate upstream issue reported by another contributor, **not** an issue created by this fork backlog, an implemented fix, or proof of an installed change. No issue comments had been posted at that check.

**Reported behavior and proposed cause, not independently reproduced here:** ROMarr's `_BsdtarSource` in `romarr/library.py` reportedly lists archive members successfully but passes a literal member path to `bsdtar -xOf` for `read`, `copy`, and `hash`. For 7z/RAR, `bsdtar` interprets characters such as `[`, `]`, `*`, `?`, and backslashes as glob syntax, so bracketed Switch release names like `Game [010012101468C000][v0][US].nsp` may fail to extract despite appearing in the listing. The reporter proposes escaping archive-member names before passing them as extraction patterns. The report describes ordinary ZIP access through Python `zipfile` as unaffected; verify actual code and fixes on the current revision before reusing that conclusion.

**Relationship to this backlog:** Issue #144 concerns *extracting a member already discovered in one 7z/RAR archive*; PR #3 concerns *discovering and selecting ROMs across multiple sibling ZIPs and literal archive-inside-archive inputs*, then validating the actual bytes and requested title. Resolving #144 alone does **not** establish sibling-ZIP discovery, nested ZIP traversal, DAT verification, or request-aware import. Conversely, a nested-archive implementation must not reintroduce member-name failures in its 7z/RAR paths. Keep the two issues separate; do not close this backlog merely because #144 closes.

**Watch / follow-up criteria:** On resumption, inspect upstream issue #144's state, maintainer responses, linked PRs/commits, merges, tagged releases and any verified release behavior. Distinguish issue closure from a merged patch, tagged release, published Docker image, or live successful import. When a candidate fix is available, inspect exact source changes and add synthetic 7z/RAR members with literal brackets and other glob metacharacters to the import regression matrix. Test `read`, `copy`, and `hash` and, when supported, nested-archive handling, without exposing ROM payloads or changing production. Do not adopt a suggested escape function without verifying how `bsdtar` treats the literal patterns and affected filenames. This relationship is tracked for investigation only; any future implementation, upstream comment, branch write or merge requires its own authorization.

**Change scope for this amendment:** Documentation-only cross-reference and watch criteria. **ROMarr code changed: NONE. Tests executed: NONE. User library/deployment changed: NONE. GitHub issue #144 independently reproduced: NO.**

## 10. November 10, 2026 PST — Upstream PR #146 overlap and remaining backlog

**Status of this record:** Documentation-only amendment. This personal-fork PR #3 remains a **draft, unmerged backlog**, not an implementation or upstream contribution. Original November 9 BlueRoms observations, hypotheses, source anchors and full test matrix above are retained as dated evidence. New source evidence below comes from a read-only inspection of the current upstream PR, **not** tests against installed ROMarr or an independent execution of the proposed patch.

### Upstream work now in progress

- [BlizzHacker/romarr PR #146 — Import archives found in download directories](https://github.com/BlizzHacker/romarr/pull/146), authored by \`dgmora\`, was **OPEN / NOT MERGED** at the November 10 readback. Inspected contributor head: \`2946a02a9b8c9fd9bec4f424dd6156a98d0b86af\`; base upstream \`main\` at \`a41b8bdeb3b52fa42dd12a16df14b84f3f037541\`. It is a proposed code change, **not a released or installed fix**.
- The reproduction uses a completed *Crazy Taxi (USA)* Dreamcast torrent whose directory contains \`Crazy Taxi (USA).7z\` alongside images, padding, metadata, and HTML. Previously ROMarr reported no Dreamcast ROM among 25 files and that an archive inside the download directory could not be imported. The contributor reports a successful import with the patch; this is **contributor-reported**, not independently reproduced here.
- The patch adds \`_DirectorySource\` in \`romarr/library.py\` to index loose files and **ZIP, 7z, and RAR archives located under a completed download directory**, retaining their per-archive member identity. Preview and import use \`source.rom_sets(platform)\`, including separate grouping of archive sources; import pre-plans destination conflicts, keeps originals for seeding, and rejects observed source-inspection/path-escape failures. Existing platform \`archive_is_the_rom\` and whole digital-installer handling are intentionally preserved.
- Added tests in \`tests/test_directory_archives.py\` and \`tests/test_disc_import.py\` cover supported archive types, multi-file CUE/BIN sets, separate source identities, loose/archived selection, destination collisions, unreadable archives and symlink escape. The contributor reported **188 focused tests passing with 2 platform-specific skips**; no tests, full suite, actual Docker build, live preview, or real release acceptance were performed for this backlog amendment.
- CodeRabbit raised review suggestions, including repeated archive listing cost, edge-case source-name collisions and other correctness/quality questions. One original destination-collision thread was marked resolved after further tests; some review threads remained unresolved on the inspected head. These are **suggestions/potential defects**, not verified bugs or evidence of full acceptance. Recheck the exact current review threads before proposing fixes.

### Precise overlap with this backlog

| Earlier backlog test/requirement | PR #146 status at inspected head | Remaining action |
|---|---|---|
| **A:** Single direct ZIP in a download | Existing behavior / regression to preserve | Verify after any upstream merge and installed release |
| **B:** Multiple sibling ZIPs in a completed folder, or directory containing an archive plus other files | **Addressed by the proposed PR #146 source logic**, including subdirectory discovery | Avoid duplicate implementation; verify merged behavior against synthetic and real sanitized layouts |
| **C–D:** Literal outer ZIP containing an inner ZIP and deeper archive nesting | **NOT IMPLEMENTED by PR #146**: it enumerates archives found as filesystem entries, not archives embedded as members of another archive | Retain separate depth-limited nested-archive feature and resource-abuse tests |
| **E, G:** Multiple candidate games and DAT-valid ROM for the **wrong requested title** | Existing source grouping/selection and DAT verification are reused; **no independently established request-title identity check** was added | Keep request-aware identity, ambiguity and selection acceptance work |
| **F, H, I:** DAT verification, UNKNOWN, corrupt/bad-dump distinction | Existing verification machinery reused; not a new independent verifier | Retain correctness tests at a pinned merged/released version |
| **J–M:** Platform exceptions, multi-track sets, selected download boundaries and destination safety | Some targeted logic/tests added, but not a blanket end-to-end guarantee | Retain focused regression/acceptance tests; avoid duplicating verified coverage |
| **N:** Symlink, member-path, nested size/depth and decompression-bomb limits | Path-containment checks added for filesystem sources; **nested extraction and full resource limits remain unproved** | Retain bounded-depth, expanded-byte, file-count, processing-time and memory safeguards |

**Important distinction:** PR #146's title and description use “archives found in download directories.” A \`.zip\` located beneath a **filesystem directory** is not the same as an **inner \`.zip\` stored as a member of an outer \`.zip\`**. Do not mark literal ZIP-inside-ZIP complete or report the original four sibling Sonic ZIPs as nested ZIP-within-ZIP. The historical BlueRoms observations in §2 remain the original evidence, not a fresh November 10 reproduction.

**Related issue #144:** [Upstream issue #144](https://github.com/BlizzHacker/romarr/issues/144) was **closed** at this November 10 check. Its 7z/RAR *member-name glob metacharacter* extraction issue is distinct from both directory archive discovery and ZIP-inside-ZIP recursion. Recheck implementation/release status before claiming the extraction issue is solved in an installed version.

### Updated next-session sequence and non-duplication gate

1. Read this entire draft PR and identical companion Markdown. Pin fresh \`BlizzHacker/romarr:main\`, fork \`main\`, active PR #146 state/head/review, related #144 status, tagged release, relevant current source and actual deployed revision separately.
2. **If #146 is open:** do not open a competing upstream issue/PR for sibling archives. Assess its actual review resolution and tests without changing the contributor's PR; retain case B as **proposed, not shipped**. If merged, rerun cases A/B and relevant J–M against the actual merged and installed build before narrowing or closing those cases.
3. Reproduce **case C: literal ZIP-inside-ZIP** independently using harmless synthetic inner/outer archives, and inspect whether current source now traverses archive members recursively. Do not infer behavior merely from the word “nested” in a PR description.
4. Retain **requested-title match vs DAT-valid-content match** as a separate acceptance requirement. A valid DAT match for a different game must not automatically fulfill a requested title. Preserve UNKNOWN when DAT proof is absent and honor selected/partial-download boundaries.
5. Only after checking whether upstream already addresses these remaining gaps, propose the smallest separate change with explicit owner permission. Use bounded archive traversal, safe member handling, regression tests, fork review/CodeRabbit gate and the established preview recovery requirements; **no automatic code or production changes**.

**Amendment scope:** PR #3 narrative and versioned companion proposal only. **ROMarr code modified: NO. Test execution: NONE. Docker/library/download changes: NONE. PR #146 merged/released/installed: NO at inspection.** Public GitHub PR #3 description and the companion Markdown must be read back as exactly identical after this update.
