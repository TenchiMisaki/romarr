> **ROMarr ZIP-import backlog — DRAFT, DO NOT MERGE.**
> This PR contains the complete investigation of multiple ZIP files in one download, ZIP-inside-ZIP support, DAT-verified game selection, and safe import. Read the full content below to resume the investigation. The same content is versioned in [the companion Markdown file](https://github.com/TenchiMisaki/romarr/blob/notes/blueroms-multi-archive-dat-import/docs/proposals/blueroms-nested-archive-dat-import.md).
> **No ZIP-import functionality has been implemented or tested by this PR.**


> **Current verified status (Nov 11, 2026 PST):** [Upstream PR #146](https://github.com/BlizzHacker/romarr/pull/146) is **MERGED** into official `main` at [`c816161`](https://github.com/BlizzHacker/romarr/commit/c816161e53da1c173aca483aedac6e05d45118bb). It implements discovery/import of ZIP, 7z and RAR archives present as files inside completed download directories (including multiple sibling archives). It is **NOT in tagged v1.8.1**, and installed/production behavior is **NOT TESTED**. Literal **ZIP-as-a-member-of-another-ZIP** traversal and independent requested-title matching remain **OPEN**. See §11.

> **Historical assessment at Nov 10, 2026:** [PR #146](https://github.com/BlizzHacker/romarr/pull/146) proposes support for archives found *in download folders*, addressing the original sibling-ZIP discovery case. Literal ZIP-inside-ZIP traversal and request-aware game identification remain separate, unverified backlog work; see §10. This backlog PR is still draft/documentation-only.

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

## 11. November 11, 2026 PST — Upstream PR #146 merged; source-level sibling-archive fix verified, remaining scope preserved

**Status of this record:** Verified read-only GitHub/source update to this **OPEN / DRAFT** personal-fork backlog; it is still **documentation-only**. This section supersedes the *then-open / proposed* PR #146 status reported in §10 without erasing that November 10 source-review history. No new ROMarr code, tests, release, Docker deployment, production configuration, download, library file, or upstream PR was changed by this backlog documentation amendment.

### 11.1 Official merge, source revision and release boundary

- [Official ROMarr PR #146 — Import archives found in download directories](https://github.com/BlizzHacker/romarr/pull/146) is **CLOSED / MERGED**, merged **2026-11-11 09:49:56 UTC (01:49:56 PST)**. Final contributor head: [`7ed9fca85afbb103f38e60b6499162c9173e9259`](https://github.com/BlizzHacker/romarr/commit/7ed9fca85afbb103f38e60b6499162c9173e9259); upstream merge commit: [`c816161e53da1c173aca483aedac6e05d45118bb`](https://github.com/BlizzHacker/romarr/commit/c816161e53da1c173aca483aedac6e05d45118bb).
- At this readback, official `BlizzHacker/romarr:main` was `c75e49381f036f6a985691e223ddc0926c094549`. Its `romarr/library.py` Git blob `70fd347c115f4f4052280d9b6d1b37acbac334fc` contains the merged `_DirectorySource` implementation. The post-merge `main` comparison did not modify that file after PR #146.
- Latest published GitHub release independently returned [`v1.8.1`](https://github.com/BlizzHacker/romarr/releases/tag/v1.8.1), published **2026-11-10 13:22:22 UTC (05:22:22 PST)**, **before** PR #146. Its `romarr/library.py` Git blob `9b8d650a5e30484d791be4018201df0a3b391588` **does not have `_DirectorySource`**. Thus **MERGED IN SOURCE: YES; INCLUDED IN v1.8.1: NO; TAGGED POST-MERGE RELEASE: NOT OBSERVED; INSTALLED/IMAGE DIGEST: NOT TESTED**. A merged patch is not an automatic tagged release or CT107 Docker update.
- The eight fetched PR #146 CodeRabbit inline review threads are all marked resolved. This is **review-thread status**, not proof of a full CI PASS, an independent end-to-end import PASS, or absence of defects. The contributor's real *Crazy Taxi (USA)* import success remains **contributor-reported** and distinct from owner-site testing.

### 11.2 Actual merged code behavior and limits

- [`romarr/library.py`](https://github.com/BlizzHacker/romarr/blob/c816161e53da1c173aca483aedac6e05d45118bb/romarr/library.py) introduces `_DirectorySource(_PathSource)`. Its constructor walks **filesystem entries** under the completed download using `path.rglob("*")`, opens eligible ZIP, 7z and RAR **files on disk** through existing archive readers, and maps each archive member to its owning source. The source's `rom_sets(platform)` groups members by owner so equal-named disc tracks from separate archives are not mixed; `read`, `hash` and `copy` delegate to the correct source.
- `_source_for` now chooses `_DirectorySource` for eligible download directories while preserving `archive_is_the_rom` and digital-installer exceptions. The preview and import paths use the same `source.rom_sets(platform)` selection. Destination preflight detects selected-name collisions before publishing, and the patch includes path-containment, unreadable-archive and duplicate-member protections.
- **The implementation does not recursively open an archive file found as a member of another archive.** Its discovery iterates filesystem entries and then member names of those entries; it does not feed an inner `.zip` member's bytes back into `_source_for` for another archive-reading layer. A directory containing `subfolder/game.zip` is **not** the same structure as `outer.zip` containing `inner.zip` containing `game.md`. Literal ZIP-inside-ZIP and deeper levels (cases C–D) remain **NOT IMPLEMENTED by this merged path**.
- No independent automatic comparison of **the DAT-identified title** against **the user's requested title** is established by this change. Valid DAT verification alone does not prove the imported game satisfies the request. Multiple legitimate candidates may still require the existing review selection; never claim one-request/one-correct-title automatic fulfillment as solved.
- Existing No-Intro/Redump `verify_set`, UNKNOWN/bad-dump distinction, platform exceptions and selected-client boundaries must continue to be exercised at the merged revision. The patch does **not** demonstrate bounded recursive extraction limits for inner ZIPs, decompression-bomb protection at multiple nesting levels, or user-site acceptance.

### 11.3 Regression evidence and backlog test disposition

Committed [`tests/test_directory_archives.py`](https://github.com/BlizzHacker/romarr/blob/c816161e53da1c173aca483aedac6e05d45118bb/tests/test_directory_archives.py) covers archive-in-directory ZIP/7z/RAR discovery; multi-track CUE/BIN import; multiple sibling archives and loose-ROM review; duplicate/case-insensitive destination conflicts; preserving original downloads; unreadable archives; and symlink escape. This review **inspected tests and code but executed no pytest, Docker import, ROM bytes, BlueRoms download, or production validation**. The November 10 contributor-reported **188 focused PASS / 2 skips** in §10 remains a prior reported test outcome, not a new independent run or a full-suite certification.

| Original cases from §6 | New status after PR #146 merge | Required next evidence |
|---|---|---|
| **A** one download folder / one ZIP | Existing direct archive path retained; regression behavior not live accepted here | Run a synthetic regression on a pinned merged build |
| **B** multiple sibling ZIPs, archive plus other loose files | **IMPLEMENTED IN UPSTREAM SOURCE**; targeted committed tests cover this flow | Confirm merged-build tests, then the owner-observed Sonic layout after a release/approved isolated test |
| **C–D** outer ZIP containing inner ZIP, deeper levels | **OPEN / NOT IMPLEMENTED by PR #146** | Separate bounded recursion design; harmless nested synthetic ZIP fixtures and security tests |
| **E, G** multiple real games; DAT-valid but wrong requested title | **OPEN / NOT FULLY VERIFIED**; source grouping/review exists, independent request-title guarantee not shown | Request-intent identity checks and ambiguous/wrong-title regressions |
| **F, H, I** DAT verification, UNKNOWN and corrupt data | Existing machinery reused; **NOT INDEPENDENTLY RETESTED here** | Exact-revision verification/error-path regressions |
| **J–M** special platforms, multi-track sets, partial selections, destinations, retries | Relevant merged checks/tests exist for several paths; **PARTIAL SOURCE/TEST COVERAGE** | Exercise untested client-identity, retry, collision, policy and platform cases |
| **N** traversal/symlink and nested resource-abuse bounds | Directory path guards and symlink tests present; **nested depth/size/time/CPU limits OPEN** | Resource and path-traversal adversarial fixtures for any future recursion |

**Separate issue:** [Official issue #144](https://github.com/BlizzHacker/romarr/issues/144) is now **CLOSED**. That 7z/RAR filename-globbing extraction concern is independent of both filesystem sibling-archive discovery and literal ZIP-inside-ZIP traversal. Do not merge its acceptance criteria with those for #146 or claim a live installed fix solely from issue closure.

### 11.4 Next-session continuation and stop conditions

1. Start by reading this full PR description and matching Markdown, current project `00`, `10`, `50`, `70`, then freshly compare official/fork `main`, the latest tagged release/image and the actual intended **test** installation. No automatic contributor-branch refresh or production deployment.
2. **Do not reimplement the already merged sibling-archive discovery**. Reuse `_DirectorySource` and its committed tests at a pinned source revision; inspect any new post-merge changes before assuming equivalence. Run harmless synthetic cases A/B and preservation/ambiguity controls on an appropriately isolated, authorized environment. Only after obtaining a build containing #146 should the historical four-Sonic-folder behavior be checked; release/install status remains a separate gate.
3. Investigate **literal `outer.zip` → `inner.zip` → ROM** and additional nesting independently. Enforce explicit depth, expanded-byte, file-count, CPU/time and containment bounds, avoid unbounded in-memory disc extraction, preserve original torrent/download assets, and keep archive-as-ROM platform behavior.
4. Independently test DAT-verification-versus-requested-title matching with one correct, multiple correct, wrong-title DAT-valid and UNKNOWN candidates, respecting the existing review/partial-download import intent. Uncertain matches should remain reviewable, not silently fulfilled.
5. Before any new implementation or public upstream report, check newly merged fixes/issues and follow current fork-only staging, exact-head tests and CodeRabbit/owner approval procedures. Current action is **STATUS DOCUMENTATION ONLY**; there is no authorization here to deploy or change production.

**Result at this November 11 documentation milestone:** **UPSTREAM MERGE: PASS (GitHub readback); MAIN SOURCE IMPLEMENTATION: PRESENT; TAGGED v1.8.1 INCLUSION: NO; INSTALLED BEHAVIOR: NOT TESTED; FULL BACKLOG: OPEN; DOCS-ONLY FORK UPDATE: intended.** This amendment does not assert full-suite success, run new code tests, or close/merge this draft backlog.

## 12. November 11, 2026 PST — Part 1 implementation opened for fork review

**Separate implementation PR:** [Personal-fork PR #10 — Archive Import Hardening: Nested ZIP Support (Part 1 of 2)](https://github.com/TenchiMisaki/romarr/pull/10), **OPEN / NON-DRAFT**, fork-only `main` → `feature/nested-zip-import-hardening`. This is **not an upstream submission**, does not close or merge this backlog, and does not authorize a production or preview deployment.

### 12.1 Why this is a two-part continuation

Official [PR #146](https://github.com/BlizzHacker/romarr/pull/146) has already merged support for ZIP/7z/RAR *files found in completed download directories*. Its single-layer archive readers did not follow a ZIP *member* that is itself another ZIP. The follow-up improves the existing import source architecture without duplicating directory discovery.

- **Part 1, now implemented on isolated fork branch for review:** limited `outer.zip → inner.zip → ROM` discovery, explicit nested-member provenance and CUE/BIN source grouping, temporary bounded staging of *intermediate ZIP files only*, existing streamed ROM hashing and copy, source download retention, archive-is-the-ROM exceptions, and review preview sizes. Boundaries enforced by the candidate: 3 ZIP layers, 16 inner archives, 10,000 member names, 256 MiB per staged inner ZIP / 512 MiB total staged, 64 GiB per declared leaf / 128 GiB total declared leaf bytes, 10,000:1 ZIP ratio, 2 MiB CUE/GDI/M3U descriptor cap; traversal, links, encrypted members, duplicate inner-container names, bad archives and depth violations fail before library publication. **Only ZIP-inside-ZIP is supported by this candidate; nested 7z/RAR remains out of scope.**
- **Part 2, not implemented or branched as part of PR #10:** request-aware import identity validation. Build on already merged upstream [PR #88](https://github.com/BlizzHacker/romarr/pull/88), checking that the DAT-identified ROM actually corresponds to the originally requested game rather than accepting any DAT-valid release. Unknown or ambiguous evidence should require review, with identity/reconciliation, partial-download and platform safeguards retained.

### 12.2 Exact current fork candidate and validation

- Baseline upstream and fork `main` were independently identical at `c75e49381f036f6a985691e223ddc0926c094549`; **fork sync not required or performed**.
- Fork PR #10 candidate head at this write: [`cac65c042d557145d5f26aab5add9f818d923b9c`](https://github.com/TenchiMisaki/romarr/commit/cac65c042d557145d5f26aab5add9f818d923b9c). Four intended files only: `romarr/nested_zip.py`, `romarr/library.py`, `romarr/import_intent.py`, `tests/test_nested_zip.py`. PR title/body/head/base and file list were read back after creation.
- **LOCAL SYNTHETIC HELPER TESTS: PASS (9/9)** against an independently staged Python 3.13 helper copy, covering 1–2 nested ZIP levels, over-depth, malformed inner ZIP, traversal, inner staging byte cap, indexed member cap, duplicate inner-container names, and two independent inner archives. **These are NOT full-ROMarr tests, and exact GitHub head integration has not been run.**
- **INTEGRATION TESTS: PRESENT, NOT EXECUTED** at this milestone; `tests/test_nested_zip.py` includes isolated preview/import, CUE/BIN, source retention, selection, unsafe content, duplicate container and archive-as-ROM regressions. Full pytest, Docker builds, image digests, private ROMs and real download-client integration: **NOT TESTED**.
- **CodeRabbit:** an automatic review began on PR #10; at initial readback the check for head `cac65c0` was **IN PROGRESS**. An earlier `c02a1f4` review was **CANCELLED** after subsequent commits, not a final review conclusion. Current-head final findings/threads/docstring percentage/quality **PENDING**. No fork GitHub Actions workflow runs had appeared for the candidate at that initial check; this is **NO RUN OBSERVED**, not a test pass or proof CI is unavailable. Recheck before reporting a milestone.
- **Deployment / mutation separation:** No official ROMarr repo, production/preview container, download data, NAS library, stored media or protected Project Knowledge/OneDrive document was changed by the Part 1 GitHub implementation. Independent preview five-minute recovery v2 remains **NOT INSTALLED/ACCEPTED**.

### 12.3 Resume instructions

First read current `00`, `10`, `50`, `70`, and **this entire backlog**, then inspect fork PR #10 **current** base/head/diff. Follow current `70` exact-head CodeRabbit+quality/threads and runtime-test gates, investigate genuine findings and correct only the isolated fork branch under standing authorization. No old review or synthetic-helper PASS certifies a newer commit. Keep PR #10 separate from this OPEN/DRAFT backlog, update this PR body and Markdown byte-identically on material milestones, and do **not** create an official upstream PR or deploy a Docker image without the applicable owner authorization. Part 2 stays a separate implementation once Part 1 reaches an independently verified, approved disposition.

## 13. November 11, 2026 PST — Part 1 CodeRabbit correction rounds (fork only)

This is a **dated continuation of §12**, not a superseding claim that the candidate is ready to merge. Personal fork [PR #10](https://github.com/TenchiMisaki/romarr/pull/10) remained **OPEN / NON-DRAFT** at the exact current feature head [`29aecbde099b3b4c7984fa8344f403950337a4fa`](https://github.com/TenchiMisaki/romarr/commit/29aecbde099b3b4c7984fa8344f403950337a4fa). Fork `main` baseline remained `c75e49381f036f6a985691e223ddc0926c094549` during implementation. Only the original four targeted implementation/test paths were modified.

The first completed CodeRabbit round on `cac65c0` posted **three actionable findings**: a cross-archive incomplete-playlist publication path (Major functional correctness), unbounded central-directory metadata parsing before enforcing ZIP entry limits (Major security), and directory entries being excluded from the count (Minor). A second round on `46dc319` added **two security findings**: ZIP64 locator metadata overrides classic values even without sentinel markers, and the outer ZIP needed its metadata preflight *before* `_source_for` opens it. All five comments were independently reviewed against source and addressed by scoped fork-branch changes; historical thread resolution/status is **not presumed**, and each new commit requires its own completed review.

**Latest candidate change:** Central-directory size/entry preflight occurs before opening either inner or outer ZIP with `zipfile.ZipFile`; directories count against the global entry budget; ZIP64 locator metadata is honored even without classic sentinel fields; nested ZIP playlist candidates are rejected if any referenced disc is missing from the *same owning archive*, in both direct and directory import grouping. Synthetic pytest cases were added for valid/incomplete playlists (including cross-archive references), directory count and byte caps, and forged ZIP64 metadata; existing source preservation, CUE/BIN separation and archive-as-ROM tests remain.

**Validation evidence:** A local isolated helper prototype passed **13/13** Python `unittest` cases on Python 3.13, plus synthetic ZIP64 negative-case inspection. The helper **was not an exact-byte copy of the committed GitHub module**, so this is **ISOLATED HELPER PASS**, **not exact-head repository-test PASS**. The tracked `tests/test_nested_zip.py` tests are **PRESENT BUT NOT RUN**, and no exact-head full pytest, Docker build, live archive import, end-to-end real download-client check or preview/production deployment was performed. The latest exact-head CodeRabbit review was **IN PROGRESS** when this amendment was prepared; **do not treat older successful/cancelled/pending checks or outdated threads as clearance**. There were no fork GitHub Actions test workflow runs observed for this candidate at inspection. Recheck fresh results and documented docstring/quality threshold before suggesting upstream action.

**Next:** Finish current exact-head CodeRabbit review and assess any further findings, execute actual ROMarr syntax + focused + risk-appropriate regression tests in the approved isolated native environment at the final SHA, confirm code review/quality/CI separately, and update the fork PR and this backlog once results are observed. **No authorization to create an official upstream PR, merge the fork PR, promote a contributor branch, or deploy ROMarr** follows from this milestone. Part 2 is still separate and **NOT STARTED**.

## 14. November 11, 2026 PST — Third CodeRabbit review and targeted corrections

Fork-only implementation [PR #10](https://github.com/TenchiMisaki/romarr/pull/10), based on verified fork `main`, received a third GitHub CodeRabbit review submission for `29aecbde099b3b4c7984fa8344f403950337a4fa` at `2026-11-11T18:03:56Z`. Its review body published **three actionable inline comments** plus **one outside-diff Major security comment**, even though the exact-head CodeRabbit check was still briefly reporting `in_progress` when polled. This is a completed *review submission*, **not** zero findings or a tested release.

**Independently inspected findings:**
- **Major ZIP safety:** a crafted ZIP comment containing another EOCD signature could make the custom preflight validate an EOCD other than Python `ZipFile`'s actual selection.
- **Major ZIP64 safety:** Python 3.13 reads ZIP64 metadata at a fixed position immediately before its locator even if the locator's offset points elsewhere. Trusting that offset could inspect the wrong metadata. The CPython v3.13.9 source was consulted.
- **Playlist correctness:** a valid same-directory reference `./Disc One.chd` was rejected by the new playlist completeness filter.
- **Test correctness:** the cross-archive playlist fixture correctly leaves the inner `.chd` as a separate selectable set; expecting the preview to be completely empty was wrong.

**Correction head (current as of this milestone):** [`4ff13040f6c0c959a1d833e2293f06a1ae4d8450`](https://github.com/TenchiMisaki/romarr/commit/4ff13040f6c0c959a1d833e2293f06a1ae4d8450) on `feature/nested-zip-import-hardening`. Changes remain limited to the previous four files. The ZIP preflight now selects Python's final EOCD signature, rejects inconsistent comment-length ambiguity, reads the effective ZIP64 record before its locator, and sequentially counts bounded central-directory entries before `ZipInfo` allocation. The playlist validator accepts a safe leading `./` without permitting unrelated subfolders/archives. Regression cases now cover those paths and correct the standalone-disc expectation. GitHub file updates were independently read back after each change; no main/upstream/protected project file or ROMarr container was modified.

**Validation boundary:** These are reviewed source corrections, **NOT a local full-ROMarr pytest PASS**. The new `tests/test_nested_zip.py` cases are committed but **have not been executed against exact head `4ff13040`**. GitHub Actions showed no exact-head test workflow runs at the first check. Current-head CodeRabbit review, measured docstring coverage, all open/outdated threads and CI must be rechecked and evaluated independently. Do not promote, merge, upstream-submit, or deploy based on this note. Part 2 request-aware identification remains untouched. `GITHUB PREVIEW: NOT VERIFIED`.

**Next safe action:** Run focused nested ZIP plus relevant existing import/regression tests in an isolated, exact-head Python 3.13 checkout; verify ZIP64/EOCD adversarial cases, CUE/M3U grouping and unchanged archive-as-ROM behavior. Evaluate the final CodeRabbit review and resolve findings only after readback, then use current `70` gates before any manual upstream PR.

## 15. November 11, 2026 PST — Fourth CodeRabbit review and digital installer correction

**Fork PR:** [#10](https://github.com/TenchiMisaki/romarr/pull/10), personal fork only, `feature/nested-zip-import-hardening` → `main`, remains OPEN/NON-DRAFT. This is Part 1 of the two-part continuation of merged upstream #146; Part 2 request-aware DAT/request matching is separate and has **NOT STARTED**.

**Fourth review:** CodeRabbit submitted its exact-head review for `4ff13040f6c0c959a1d833e2293f06a1ae4d8450` at `2026-11-11T18:20:08Z`, identifying a **Major Data Integrity & Integration finding** (PC/Windows digital installer contents spanning outer and nested ZIP layers were incorrectly grouped per container), plus a **Minor, explicitly UNVERIFIED** finding suggesting independent disc candidates be reselected after an incomplete playlist is rejected. CodeRabbit's published summary also reported **Moderate** merge risk and **95.83%** scoped Python docstring coverage versus **80.00%** required, **for the earlier reviewed head `4ff1304` only**. A review submission is not a clean review, test pass, or merge approval. At the follow-up poll the CodeRabbit check still read IN PROGRESS despite the published review submission.

**Major finding independently confirmed from source:** `romarr/selection.py:_digital_set()` intentionally groups an entire Windows installer (`setup.exe`, its accompanying `.bin` data and other content), but the nested ZIP source called `pick_all_rom_sets` independently for every owning ZIP. That could cause multiple mutually dependent installer groups or destination collisions. Under existing personal-fork staging authority, `_NestedZipSource.rom_sets` was corrected to pass **all nested ZIP members as one digital ROM set** when `platform.media == "digital"`, while retaining ZIP-specific grouping for disc platforms. A new regression test constructs an outer ZIP with `setup.exe` and an inner ZIP with two data files, asserts one preview set/selection and complete staged import, and verifies that the original source is unchanged.

**Minor finding disposition:** The request to reselect ostensibly unrelated standalone disc content after an incomplete M3U playlist is **UNVERIFIED and deferred**, because the importer has no trustworthy basis to distinguish an unrelated disc from a missing/partial disc set once a referenced playlist is invalid. Existing fail-closed behavior and incomplete-playlist rejection were preserved; no silent fallback into an automatically imported incomplete game was added. Reassess with a proven safe identity decision or explicit reviewed-selection workflow rather than assuming the loose member is unrelated.

**Current implementation head as of this note:** [`46d5bbcba309da08207d70c3e2524bb74ae8a870`](https://github.com/TenchiMisaki/romarr/commit/46d5bbcba309da08207d70c3e2524bb74ae8a870). Source and test GitHub writes were read back byte-for-byte. The actual source/test diff still has **four affected paths**: `romarr/nested_zip.py`, `romarr/library.py`, `romarr/import_intent.py`, `tests/test_nested_zip.py`; no fork `main`, upstream branch, live production/preview Docker, library or download files, or protected Project Knowledge/OneDrive documents were changed. Fork PR #10 title and description are maintained separately.

**Verification limits:** Latest-head CodeRabbit was **IN PROGRESS** when inspected, earlier review/95.83%-coverage does not certify `46d5bbc`. Actual exact-head syntax + focused/full ROMarr `pytest`, Docker build/API, live download-client behavior, preview and production remain **NOT TESTED**. GitHub had **no fork test workflow run observed**. The intended trusted nonlogin Python 3.13 test workspace in CT107 is an independent execution gate with identity, resource and production-isolation checks; no guest test was run by this GitHub-only work. Next: inspect exact-head CodeRabbit outcome and all review threads, run genuine regression tests in the approved isolated worktree when targeting can be independently verified, then reassess readiness. Do not submit an upstream PR, merge, or deploy without the separate applicable owner gates.

## 16. November 11, 2026 PST — Deferred investigation: aggregate archive resource limits and platform-specific thresholds

**Status: BACKLOG / INVESTIGATE ONLY — NOT IMPLEMENTED, NOT TESTED.** Added at owner request after reviewing the resource limits of Part 1 [fork PR #10](https://github.com/TenchiMisaki/romarr/pull/10). This item **does not expand PR #10's active implementation scope or block its independent review/test gates by itself**. No new code, deployment, GitHub Actions configuration, or live host check is authorized by this addition. Part 2's request-to-game/DAT matching remains a separate implementation effort. Revisit this once Part 1 has an exact-head test and review baseline, or sooner only if evidence demonstrates an urgent resource-safety issue.

### 16.1 Observed implementation versus unverified behavior

**Source verified at fork PR #10 head `46d5bbcba309da08207d70c3e2524bb74ae8a870`:**
- `romarr/nested_zip.py` defines constant archive-inspection ceilings shared across platform types: 3 ZIP layers, 16 inner ZIP containers, 10,000 total entries across one indexed archive tree, 256 MiB per staged inner ZIP, 512 MiB combined staging for that tree, 64 GiB declared size per leaf, 128 GiB combined declared leaves, 10,000:1 per-member compression ratio, 2 MiB per CUE/GDI/M3U descriptor, and 16 MiB of central-directory metadata **per archive**. The `NestedZipIndex` instance tracks its own inner-archive count, staged bytes, expanded bytes and examined entries.
- Those counters are **per index / nested archive tree**, not a shared application-wide allocation; separate source inspections may each obtain their own allowance. The `check_zip_central_directory` preflight is applied to an individual ZIP. The implementation inspected does **not** establish a global memory, CPU, temporary-disk or simultaneous-inspection budget.
- `romarr/platforms.py:Platform.max_size` is a separate, existing *release selection* property, set by platform. It is **not** the nested ZIP decompression, staging or concurrency budget. Special `archive_is_the_rom` platforms must retain their no-extraction behavior.
- **NOT YET VERIFIED:** how many archive inspections can actually run at once across preview, scheduled import, user-triggered imports, background jobs or different worker/process instances; peak memory/disk/CPU under concurrency; whether temporary data persists longer than the request; whether the current bounds reject ordinary legitimate content. These need source call-path review plus controlled measurements, not inference from the constants.

### 16.2 Investigation work

1. **Trace actual scheduling and lifetime.** Inspect the preview/import call paths, worker/process model, job concurrency, cancellation and cleanup. Identify where simultaneous `NestedZipIndex` objects can coexist, including independent processes; establish if any existing concurrency or resource governor already covers them before proposing a new one.
2. **Quantify aggregate worst cases and observed usage.** Estimate maximum simultaneous scratch allocation and metadata/memory costs at a plausible number of active inspections; then measure CPU, RSS, temporary storage, peak open files, processing time, cancellation cleanup and production-service impact using small, reproducible synthetic archives in an appropriately isolated test environment. Preserve actual test counts and pinned SHA. Do **not** stress-test a production container simply because a local source test workspace shares it.
3. **Assess global backpressure only if warranted.** Compare (a) no new governor with monitoring, (b) a small bounded worker/semaphore limit, (c) a global shared scratch-byte budget with queuing/reservations, and (d) separate per-worker plus cross-process coordination if the app truly has multiple processes. Determine whether a waiting job gets a bounded queue, a clear retryable result, or a fail-closed rejection. Avoid arbitrary latency or introducing a service/daemon without demonstrated need.
4. **Review threshold policy, including platform types.** Check whether current fixed ZIP safety limits appropriately support cartridges, multi-disc sets and PC installer releases; evaluate false rejection of large but legitimate content, tiny malicious archives with extreme expansion, and archive-is-the-ROM exceptions. Treat platform-aware tuning as **an option to justify with evidence, not the default**. Preserve strict universal security ceilings even if a specific platform needs an adjusted legitimate-size policy; never derive a safe decompression allowance solely from `Platform.max_size`.
5. **Propose observability if needed.** Define resource-cap hit counters, active queued/running inspection counts, bounded temporary disk usage, clear user-facing failure categories and cleanup telemetry. Ensure logging avoids ROM/file metadata exposure beyond existing sanitized policy and does not turn normal processing into log flooding.

### 16.3 Proposed acceptance tests and decision record

- Baseline and compare **one versus two/four simultaneous** synthetic inspections, including combinations of small nested cartridges, multi-disc descriptors and large multi-file Windows-style installer fixtures. Explicitly label any unsupported parallelism rather than manufacturing it.
- Exercise near-bound and over-bound ZIP depth, member count, directory metadata, ZIP64, staging-byte and expansion budgets, malicious ratios, cancellation, failed inspection, disk-pressure and worker restart/retry. Confirm cleanup and no partially published library members on failure.
- Verify source download retention, independent sibling archive trees, disc/playlist grouping, and `archive_is_the_rom` platforms remain unchanged. Cover application restart or multi-worker behavior **only where architecture and a safe isolated harness support it**.
- Record observed peaks, resource headroom, whether failures are correctly scoped per download or across concurrent jobs, proposed threshold/configuration policy, security rationale and measurable tradeoffs. Decision can be **KEEP CURRENT**, **ADD GLOBAL CONCURRENCY/RESOURCE BUDGET**, or **PROPOSE PLATFORM-SPECIFIC THRESHOLDS**; no answer is predetermined.
- **Completion criterion:** a dated, source-grounded decision with reproducible benchmark/regression evidence, explicit safe defaults, behavior under resource exhaustion, recovery implications, and a separately scoped implementation/review PR only if a change is justified and authorized. Do not silently append a resource-governor change to the already-open Part 1 or Part 2 PR.

**Continuation/recovery:** First read this backlog's full prior history and current `00`/`10`/`50`/`70` references, then verify live upstream/fork main and Part 1's final SHA/review/test disposition. Inspect current archive resource logic and actual worker topology before executing any benchmark. Protect application and download/library data. This is documentation of a future study, not proof of current memory exhaustion, a production defect, or acceptance of a new implementation.

## 17. November 11, 2026 PST — Owner sequencing decision: include resource-limit investigation in Part 2 planning

**Owner decision:** The concurrent archive-resource and platform-limit investigation in §16 is now **explicitly included in Part 2's research, acceptance planning and pre-implementation review** rather than treated as a disconnected future reminder. This is an amendment to §16's scheduling only: it **does not change** the two existing implementation goals, authorize an unreviewed resource-governor implementation, or imply the analysis/tests are complete.

**Part 1 — unchanged current scope:** Safely support nested ZIP discovery, existing archive import semantics, streamed verification and source-retention guarantees through [personal-fork PR #10](https://github.com/TenchiMisaki/romarr/pull/10). Its CodeRabbit findings, exact-head tests and current resource-safety vulnerabilities remain Part 1 acceptance gates. Any proven severe security or memory-exhaustion issue must be corrected or explicitly blocked **before** Part 1 is proposed upstream; do not defer an actual safety defect merely because the broader concurrency study is scheduled with Part 2.

**Part 2 — expanded planning/verification checklist, one primary code goal:**
1. **Primary development:** Validate that an identified/DAT-verified ROM is the game actually requested, reusing existing request identity and title-reconciliation logic; fail closed or require explicit review for ambiguous or wrong matches.
2. **Resource/concurrency investigation (incorporate §16):** Before finalizing the Part 2 design, trace how preview/import jobs run concurrently across process/worker contexts and identify the lifetimes and aggregate resource costs of independent archive inspections. Distinguish per-leaf, per-inner-archive, per-tree, per-ZIP-directory and true application-wide limits. Verify how current global constant defaults interact with different platform media types and existing `Platform.max_size` release-selection policy. Measure representative cartridge, disc/playlist and Windows installer fixture behavior where a safe test environment supports it.
3. **Risk-based decision:** Record whether the observed configuration can remain **KEEP CURRENT**, requires a **GLOBAL CONCURRENCY / TEMPORARY-DISK BUDGET**, or supports **PLATFORM-SPECIFIC THRESHOLD CHANGES** with separate immutable security ceilings. Document the evidence, legitimate-release false positives, max resource usage, queue/retry/fail-closed behavior, cleanup/cancellation and operational tradeoffs.
4. **Implementation boundary:** Make **request-aware matching** the cohesive Part 2 implementation/review PR. If the resource study shows a small tightly coupled guard is essential to that behavior, explicitly justify its inclusion and broaden tests/code review; for an independent concurrency scheduler, configuration surface, or widespread platform-limit change, create a **separate, scoped follow-up implementation PR** rather than silently folding it into Part 2.
5. **Acceptance and handoff:** Link the measured resource study/decision and any pending follow-up to Part 2's review checklist. Report separately what was merely inspected, syntactically checked, actually tested, reviewed by CodeRabbit, upstream accepted, and deployed. Part 2 cannot claim completion of the *investigation* without the §16 evidence, but a new global governor is **not automatically required**.

**Sync/status at this planning amendment:** Upstream `BlizzHacker/romarr:main` and personal fork `TenchiMisaki/romarr:main` were independently confirmed identical at `c75e49381f036f6a985691e223ddc0926c094549`. **SYNC CHECK: PASS (IDENTICAL); SYNC APPLIED: NO (NOT NEEDED).** The existing implementation PR #10 is still separate/open on the fork; this is a **documentation-only** change on the original backlog notes branch, with no source, deployment, official upstream or protected Project Knowledge/OneDrive modifications. Previous Section 16 technical detail and historical record remain authoritative for the future study; this section specifies when and how to work it into Part 2.

**No test claims:** The resource-concurrency investigation, benchmarks, configured global shared budget, and platform-aware policy changes are **NOT TESTED / NOT IMPLEMENTED** by this plan update.
