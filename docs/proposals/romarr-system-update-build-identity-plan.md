# Backlog: ROMarr System → Update — Build Identity, Correct Update Status, and Docker Guidance

> **DRAFT / PERSONAL FORK ONLY — DOCUMENTATION AND PLANNING, DO NOT MERGE.** This is a parent handoff for future narrowly scoped implementation PRs. No executable source, workflow, release, private infrastructure, or deployed application was changed. No approval to implement, merge, publish upstream, or deploy is implied.

## Purpose and requested behavior

Preserve ROMarr's **existing System → Update page**, including its card order, theme, controls, and optional sections. Improve only what is missing or misleading: recognizable development-build identity instead of 0.0.0+unknown; a truthful update verdict; accurate update capability for Docker versus Git installs; safe container-update instructions; and consistent update-check behavior.

The owner's visible requirements are: keep the current **This install** three-tile layout, show a compact Development/Release designation and source branch/short SHA, keep the **Automatic updates** table and its current action buttons, retain **How to update this container**, **ROM Hub plugins**, and **Last self-update log** where applicable, and do not invent a Docker self-update button. A screenshot of the proposed existing-layout adjustment is embedded below.

## Proposed rendered mockup — illustrative, not a live screenshot

![Proposed ROMarr System Update page showing existing three version tiles, one compact development line, existing update settings and controls, Docker guidance and the optional ROM Hub plugin table](https://raw.githubusercontent.com/TenchiMisaki/romarr/notes/romarr-system-update-version-identity-plan-20261110/docs/proposals/assets/romarr-system-update-page-proposed.svg)

[Open the rendered mockup](https://raw.githubusercontent.com/TenchiMisaki/romarr/notes/romarr-system-update-version-identity-plan-20261110/docs/proposals/assets/romarr-system-update-page-proposed.svg) — source SVG under docs/proposals/assets in this same branch. Values such as version 1.8.1, branch main, revision a41b8bd, status ON and the sample plugin row are **illustrative, not measurements of a running container**. In particular, the sample plugin row is not evidence that that plugin is installed.

**UI delta only:** add a small Development indicator and Build / Branch / Commit text to This install; distinguish **indeterminate** update status from **no**; show **Not supported in Docker** in the existing Auto-apply row when the install is containerized; keep the existing button visibility rules. Do not move settings into this page, duplicate Settings → General, add tabs, or restyle the navigation.

## Pinned audit inputs and current evidence — November 10, 2026

- Official source: [BlizzHacker/romarr main](https://github.com/BlizzHacker/romarr/tree/a41b8bdeb3b52fa42dd12a16df14b84f3f037541), commit a41b8bdeb3b52fa42dd12a16df14b84f3f037541. Personal fork TenchiMisaki/romarr main was independently re-read at the identical commit, ahead/behind 0/0; the documentation branch was based on this exact ref.
- Latest official GitHub release retrieved at investigation time: [v1.8.1](https://github.com/BlizzHacker/romarr/releases/tag/v1.8.1), published 2026-11-10 at 13:22 UTC. A release tag is not proof of the installed Docker image or of any host-side update.
- Owner-reported symptom: a developer Docker build displays **0.0.0+unknown**; the production image did not automatically adopt newly published v1.8.1. Installed image tag, digest, deployment method, actual host-side updater and production runtime SHA were **NOT independently collected**. A previously documented pinned release tag makes non-advancement plausible, but this is **not** a verified current root cause.
- Duplicate search: no matching open upstream issue/PR found with the queries used on 2026-11-10; this is a scoped search, not a proof that no similar issue exists anywhere.
- Read-only code inspection included: [UI renderer](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/ui.py), [service/check/update API](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/app.py), [version resolver](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/version.py), [Git/Docker updater](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/selfupdate.py), [scheduler](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/scheduler.py), [settings defaults](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/romarr/store.py), [Docker CI](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/.github/workflows/docker.yml), [update regression tests](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/tests/test_selfupdate.py), and [version tests](https://github.com/BlizzHacker/romarr/blob/a41b8bdeb3b52fa42dd12a16df14b84f3f037541/tests/test_version.py).
- Related packaging paths were inspected for limited version-parity implications: both Dockerfile variants, Windows desktop build script, Proxmox CT installer and update scripts. **No live systems, images or tests were executed** during this plan.

## Verified existing behavior and source-derived findings

| ID | Finding / distinction | Basis | Severity / handling |
|---|---|---|---|
| F1 | Four Docker CI build-arg placements pass the release tag for tagged builds, but 0.0.0+unknown on non-tag builds. Both Dockerfile variants bake that value into a generated Python version file; the version resolver otherwise checks installed distribution metadata and environment. No revision/build-provenance metadata is exposed to the Update page. | docker.yml, Dockerfile, Dockerfile.browser, version.py | Functional build identification gap; preserve unknown fallback when no trustworthy source exists |
| F2 | The This install cards show running_version, cached latest_version and a Boolean update_available. The Update API also reports install shape, optional Git branch/SHA, update settings, optional plugins and log. For Docker, detect() returns container identity before checking for Git and thus does not report source branch/SHA. | ui.py RENDER.update, app.py update_status, selfupdate.py detect | Do not assume a Docker runtime has .git; add verified build metadata |
| F3 | The unknown-version guard correctly avoids misleading notification/update application, but stores update_available=false. The UI renders false as **no**, which can falsely imply the install was checked and found current. Network/API errors likewise do not have a persistent last-check result/time on the page. | app.py check_update, update_status; ui.py | Fix the API/UI distinction: available / current / indeterminate / check failed / not yet checked |
| F4 | Daily UpdateCheck is registered at 86400 seconds when enabled. Its check_update() reads the upstream latest **release** endpoint regardless of configured stable/nightly. A changed main-branch SHA without a new release will not trigger the automatic nightly updater. | app.py scheduler registration, check_update, apply_update, selfupdate.resolve_target | Separate nightly revision discovery/decision from stable release comparisons |
| F5 | With auto_update true, **Check now** invokes check_update(), which can call apply_update() if a newer version is found. A control labeled Check now can therefore initiate a Git updater/restart rather than a read-only comparison. | ui.py button, app.py run_command/check_update | Make explicit manual check non-mutating; keep automatic application a distinct scheduled policy |
| F6 | Git installs can self-update by ff-only Git operation with download/import busy checks and detached restart script. Docker installs cannot update themselves. The automatic-apply setting is nevertheless shown as configured ON/OFF without an effective capability state; enabling it on Docker can repeatedly attempt an impossible apply. | app.py apply_update; selfupdate.detect; store.py | Clearly separate configured intent from effective eligibility |
| F7 | Docker help hard-codes ghcr.io/blizzhacker/romarr:latest and suggests pulling, stopping and removing a container without knowing the host's actual pinned image, Compose definition or rollback state. That is not safe as a universally applicable copy/paste procedure. | selfupdate.docker_guidance, ui.py | Replace with non-destructive deployment-aware guidance; do not run Docker host actions from inside ROMarr |
| F8 | Git update script allows a checkout fallback to main, uses destructive git reset --hard on dependency failure, logs restart failures as warnings, and reports launch success before post-restart health is checked. A clean-worktree/branch/rollback/restart acceptance gate is missing from this path. | selfupdate.build_script/launch | Higher-risk, separate safety PR with failure/recovery regression cases |
| F9 | Plugin updates are independent of ROMarr image updates. Plugin schedule has its own setting; Update plugins now appears only when plugins are present. The plugin table and Git self-update log are conditional. | app.py, hub integration, ui.py | Preserve the existing separate plugin lifecycle |
| F10 | Proxmox installer/updater parse an obsolete hand-typed VERSION assignment that no longer exists; Windows desktop packager defaults to 1.8.0 and has no proven generation of embedded backend version metadata. | proxmox/ct/romarr.sh, proxmox/ct/update.sh, scripts/build-windows-desktop.ps1 | Version-consistency follow-up; runtime behavior needs independent tests |

### Important distinctions

- **Build provenance** (release or development, source ref, full commit, build method and timestamp if provided) is not the same as **update channel** (stable or nightly policy), install mechanism (Git/Docker), or the operator's configured auto-apply preference.
- A developer image built from the same commit as a release may show a valid base release plus Development/SHA. A newer branch commit must not be mislabeled as a published release. Do not infer a base version solely from a moving main image tag or a stale package default.
- A **development** label does not automatically permit release comparison or unattended updates. Use an explicit validated update-eligibility policy; fail closed for genuinely unidentified builds.
- A Docker container can **check and notify**, but replacing a running image requires a **host-side deployment mechanism** with its own authorization and recovery controls. ROMarr plugin updates remain a separate concern.
- All UI values in the screenshot are proposed illustrative states, not measured runtime facts. The proposed check verdict must use real newly collected evidence, not the image's example no.

## Proposed child PR implementation plan

### PR 1 — Build identity and Docker provenance (foundation)

**Scope:** Extend the Python version/build metadata model with separate fields for release/base version, build type (release/development/unknown), source repository/ref and exact commit. Generate validated metadata in GitHub Actions for **both image variants**, including tagged and untagged builds, and expose it through the existing backend status/update responses. Preserve the present version-derivation precedence and backwards compatibility for installed distributions and source checkouts. Include a provenance distinction for developer builds; never guess a release number for unidentified sources.

**Tests:** Metadata precedence and malformed inputs; tag versus main/PR/locally built images; two Dockerfiles and all four CI argument placements; no .git in image; wrong/unknown source version; genuine release-tag behavior. Existing unknown-version safety tests must remain green. Confirm OCI revision labels or equivalent provenance are correct if introduced.

**Depends on:** none. **Status:** PROPOSED / NOT IMPLEMENTED / NOT TESTED.

### PR 2 — Correct update-check semantics and API status

**Scope:** Return explicit status fields for last successful check, last error, comparator reason, availability state, install capability and effective auto-update. A manually clicked **Check now** is strictly check-only. Stable checks compare valid release versions; nightly checks use verified source/remote revision identity, not merely the newest stable tag. Never auto-apply Docker images. Keep settings under Settings → General; do not silently change user preferences, schedule or automatic plugin behavior.

**Tests:** Current/newer/unknown/failed/unreachable/rate-limited states, stale cached flags, disabled checks, developer build with known/unknown base, main commit advance without a new release, two channels, check-only manual action, Docker auto-apply configured ON but effective OFF, notifications no more than once per release, busy queue. Verify old API consumers/Stats call sites and backward-compatible status shape.

**Depends on:** PR 1 for identity fields. **Status:** PROPOSED / NOT IMPLEMENTED / NOT TESTED.

### PR 3 — Git/source self-updater safety and recovery

**Scope:** Explicit expected source branch and clean-worktree preflight; reject ambiguous checkout and mismatched target; remove silent fallback to main; avoid destructive rollback of operator-owned tracked changes; validate ref/tag ancestry and shell/path handling; preserve dependency rollback; surface service restart/health failure honestly. Retain queue busy/defer and ff-only guarantees. This PR changes **Git/source installation behavior only**, not production Docker hosts.

**Tests:** Dirty checkout, detached HEAD, unexpected branch, invalid target, preflight identity/permissions, missing prerequisites, failed fetch/merge/pip/restart/health, a successful restart and recovery from each partial state. Shell execution tests should use disposable fixtures, not a live service.

**Depends on:** independent of UI; coordinate API failure states with PR 2. **Status:** PROPOSED / NOT IMPLEMENTED / NOT TESTED.

### PR 4 — Minimal existing-page UI and deployment guidance

**Scope:** Small, focused changes to the existing RENDER.update markup: preserve This install three tiles, add compact build line and development marker, make unknown/error states legible, retain Automatic updates four rows and current actions, show Docker auto-apply as **not supported**, and replace generic destructive Docker commands with accurate deployment-aware guidance. Keep optional plugin table and Git log unchanged unless data requires a correction. Preserve theme, mobile layout, accessibility and escaping of source fields.

**Tests:** Existing DOM/page shape, three tiles/section order, release/dev/unknown variants, Docker/Git/unknown install types, button presence and handlers, malicious metadata escaping, plugin table conditional, log conditional, narrow/mobile/dark/light/warm appearances, screenshots and responsive regressions.

**Depends on:** PRs 1 and 2; may link PR 3 if Git capability messages change. **Status:** PROPOSED / NOT IMPLEMENTED / NOT TESTED.

### PR 5 — Other installer/version parity, only after scoped verification

**Scope:** Remove the obsolete Proxmox VERSION sed parsing, use generated/runtime version metadata for GitHub tarball/source installs, and check the Windows packager's independent version defaults and embedded Python backend. Coordinate with the maintainer's release process rather than hand-changing version constants without verification.

**Tests:** Installer/update reporting for release tarball and main source, Windows packaged backend and desktop app identity, missing metadata, pinned tag and rollback. No real Proxmox guest changes are authorized by this parent.

**Depends on:** PR 1. **Status:** PROPOSED / NOT IMPLEMENTED / NOT TESTED.

### Separate optional owner-side work — Docker host auto-update

This is **not an upstream ROMarr self-update PR** and is not authorized by this backlog. First inspect the private host's actual Docker deployment, pinned tag, image digest, compose/service definition, existing pull/check automation, backups and rollback method read-only. Then separately decide whether to use a supported host image-updater/Compose workflow, with opt-in update policy, preserve-all mounts/credentials, change window, health verification and rollback. A release being published does not automatically advance a pinned image. Never inject a privileged Docker socket into ROMarr simply to make the web button work.

**Status:** OPTIONAL / SEPARATE OWNER APPROVAL / CURRENT HOST STATE NOT VERIFIED.

## Acceptance contract for the overall work

- [ ] A release image reports its true release version without a hand-maintained app.py constant; development images report honest build/source provenance.
- [ ] The Update page preserves its current card order, three-version-tile layout, theme, controls and conditional sections shown in the mockup.
- [ ] Available/current/unknown/not-checked/error states are visibly distinct, with evidence-backed last successful check and error details.
- [ ] Docker containers never claim they can install/recreate their own image. A configured preference cannot be mistaken for executable capability.
- [ ] A manual **Check now** never implicitly applies an update or restarts a Git install.
- [ ] Stable checks honor validated release comparisons; nightly checks can detect main-commit advances independently of release tags without false release notices.
- [ ] Automatic Git applies require explicitly configured opt-in, correct target, idle queue, safe ff-only update, verified restart and recoverable failure path.
- [ ] Plugin update scheduling/manual action and log sections remain independent and behave as before.
- [ ] Docker guidance does not assume latest, silently change a pinned image, or suggest deleting a container absent verified recovery context.
- [ ] Relevant version, API, update, UI and packaging tests pass against each **exact final** child PR head; CI/CodeRabbit results, when run, are individually verified. No previous unrelated PASS transfers to a new SHA.

## Remaining unknowns and safe next session

1. Read this complete draft PR and its same-content Markdown, then current Homelab 00, 10, 50 and 70 before any implementation or host work. Recheck official and fork refs; the pinned audit is dated, not evergreen.
2. Read exact current affected source, tests, upstream releases and potential duplicate issues/PRs. Validate the current image/version mismatch on actual development and production images **read-only** before treating the pinned-tag explanation as the cause.
3. Decide whether source-only build metadata is enough or whether a separate immutable image build identifier/repository is necessary; do not let an update channel masquerade as source provenance.
4. Implement child PRs using **separate approved branches** and the documented **owner-manual non-draft fork PR submission** and exact-head CodeRabbit/testing gates. Do not turn this backlog draft into a code-bearing staging PR.
5. No live Docker/Proxmox change until exact host/guest, paths, credentials, backups and accepted preview recovery protections are verified and separate permission is obtained. Private infrastructure identifiers and secrets must stay out of public PR comments/docs.
6. If child PRs are merged, append a dated progress register and actual links here; keep the PR body and Markdown synchronized. Do not silently mark a proposed item shipped or merge this planning PR just to make the backlog disappear.

## Verification and publication register

| Date | Evidence | Classification |
|---|---|---|
| 2026-11-10 | Read-only GitHub fork/upstream main identity and compare: both a41b8bdeb3b52fa42dd12a16df14b84f3f037541, 0/0 | PASS — source ref equality at capture time |
| 2026-11-10 | Read-only review of update UI, backend, scheduler, version, Docker, Git updater, plugin integration and applicable tests | REVIEWED — static source only; no test execution |
| 2026-11-10 | Release v1.8.1 observed via official releases endpoint | OBSERVED — not a runtime or deployed image result |
| 2026-11-10 | Proposed existing-layout screenshot generated from audited names/card order | ARTIFACT — illustration, not a captured live browser |
| 2026-11-10 | Actual developer/prod Docker image digest, live version, auto-updater deployment and host health | NOT VERIFIED |
| 2026-11-10 | Focused/full automated tests, build, installation, UI browser/Preview, CodeRabbit and new release checks | NOT TESTED / NOT PERFORMED |
| 2026-11-10 | Scope of this PR: two new files, documentation/illustrative SVG only | MUST VERIFY AFTER PUBLICATION |

**Status:** Parent plan/backlog only. Source changes, GitHub upstream contribution, runtime validation, deployed updates, protected Homelab reference publication and private host-side automation are **NOT PERFORMED**. **Recovery:** leave this draft unmerged; if a factual error is found, correct only through a separately authorized dated Markdown/PR-body update while preserving prior evidence.


---

## 2026-11-10 audit supplement — lessons from the earlier fork review and Sidebar v26 validation

> **Latest dated supplement.** This section supersedes earlier statements that no child implementation branch exists, while preserving the original November 10 baseline findings and five-PR plan above. No change to approved visual layout, code deployment policy, owner-manual implementation PR creation, or private recovery boundary.

### A. Current implementation progress and source identity

- **PR 1 implementation candidate exists on an isolated fork branch**: [`feature/romarr-build-provenance-pr1`](https://github.com/TenchiMisaki/romarr/tree/feature/romarr-build-provenance-pr1), head [`631933ccb57fa257b3b92bbdc0ec66be46a77a00`](https://github.com/TenchiMisaki/romarr/commit/631933ccb57fa257b3b92bbdc0ec66be46a77a00), based on `a41b8bdeb3b52fa42dd12a16df14b84f3f037541`. Six files changed: `.github/workflows/docker.yml`, both Dockerfiles, `romarr/app.py`, new `romarr/build_info.py`, and new `tests/test_build_info.py`. Fork/upstream `main` still matched at the pinned base during this audit. **No non-draft PR was found for this implementation branch, and no merge/deployment is claimed.**
- Static independent source readback finds two `get_build_info(VERSION)` API additions, each Dockerfile generating an optional `_build_info.py`, four pairs of CI build inputs (standard/browser × smoke/push), and build-identity smoke statements in both image workflows. The new unit-test file defines **10 test functions**, not 10 independently executed passes. **Actual full pytest, real Docker image build/boot, authenticated API behavior, CodeRabbit and browser rendering remain NOT TESTED by this audit.** The prior conversation reported eight isolated focused checks, but no reproducible test-run artifact or exact environment was independently collected here; do not promote that report to full-suite PASS.
- **Expected intermediate behavior:** PR 1 records development source provenance but intentionally preserves an **unknown release version** for non-tag builds. It does **not** yet replace the `0.0.0+unknown` Running tile or alter update eligibility. PR 2 and PR 4 remain necessary, and their changes must not pretend every developer revision is an official release.
- **PR source identity caveat:** for a GitHub `pull_request` workflow, `github.sha` may identify the synthetic tested merge commit (`refs/pull/.../merge`) rather than the contributor head commit. That is valid **built-image provenance** but must not be mislabeled as the author's branch HEAD. Proposed future API/UI tests should explicitly distinguish tested revision, base/head and ref type.
- The neighboring [UI-consistency backlog PR #4](https://github.com/TenchiMisaki/romarr/pull/4) remains the owner of global/header/sidebar, responsive and accessibility consistency. This PR #6 owns **Update-domain version/status semantics and minimal Update-page markup**; a dated cross-reference was requested for PR #4. Avoid a second global redesign or duplicate implementation of existing UI-01/UI-02 fixes.

### B. Reusable findings from previous fork audits — not blanket source-test proof

- Prior [fork review PR #1](https://github.com/TenchiMisaki/romarr/pull/1) and [upstream PR #140](https://github.com/BlizzHacker/romarr/pull/140) exposed persistence-failure behavior, stale-result/ordering issues and lock boundaries under concurrency. Their specific Metadata and library defects **do not imply ROMarr's updater has the same defect**. Reuse the audit **method** (inspect actual interleavings and durable-state failure paths), not its fixes or previous PASS counts.
- The owner's prior Sidebar v26 validation report dated November 6 enumerated 283 tracked files and surveyed 51 Python package modules at **older upstream `3ba7105`**; 103 scripted local checks were reported for that sidebar candidate, and live patched-app/full-suite/Safari verification was expressly absent. That is historical **scope/coverage evidence**, not a fresh full-code or current Update-page test at `a41b8bd`.
- Fork [backlog PR #4](https://github.com/TenchiMisaki/romarr/pull/4) and [official UI PR #145](https://github.com/BlizzHacker/romarr/pull/145) demonstrate the value of testing the actual committed DOM at desktop/mobile widths. UI-01/UI-02 are already merged/released; the System → Update page must retain its own current existing card and button structures.
- CodeRabbit's green GitHub check means review completion, **not** zero actionable comments. The correct gate is final **exact head** + all issue comments/threads + actual applicable tests + independent upstream lifecycle verification. Backlog drafts are not auto-reviewed by default; do not convert this planning PR to non-draft merely to solicit the bot.

### C. Expanded audit of update concurrency — source-derived risk, not reproduced failure

**Call paths on the pinned `a41b8bd` source:**

1. `ROMarr.__init__` registers scheduled `UpdateCheck` at 86,400 seconds and starts the Scheduler thread (`romarr/app.py`). `romarr/scheduler.py` serializes only its own scheduled jobs; it does not serialize independent HTTP command requests against the same operation.
2. HTTP `POST /api/v1/command` invokes `ROMarr.run_command('UpdateCheck')` → `check_update()`; the UI's **Check now** uses this endpoint. A user with `auto_update=true` can implicitly invoke `apply_update()` in that path. Separate `ApplyUpdate` command can also invoke `apply_update()`.
3. `apply_update()` takes `self._lock` for a queue snapshot/busy test, **releases it before** `selfupdate.launch()`, and has no demonstrated cross-call single-flight/in-progress guard.
4. `selfupdate.launch()` writes a fixed `.romarr-selfupdate.sh`, truncates a fixed `.romarr-selfupdate.log`, and starts a detached process. Overlapping launches could rewrite a script/log another process is about to consume. This is a **plausible correctness/safety race from the source interleaving**, not a runtime-reproduced incident.

**Required addition to PR 3 (do not create PR 6):** introduce an update-specific **single-flight gate** spanning decision, launch and detached completion/restart, with explicit already-running/deferred reporting, tested atomic ownership/cleanup, and no shared script/log overwrite. Consider safe cross-process coordination across restart instead of relying only on an in-memory mutex. Preserve the existing import/download queue guard, non-force target identity, and clean-worktree/rollback requirements. Do not use a generic blanket lock that blocks normal API requests or silently retries unsafe launches.

**Concurrence and fault-injection matrix to add before promotion:**

| Case | Required result | Current evidence |
|---|---|---|
| Two simultaneous `ApplyUpdate` POSTs | At most one detached launch; second receives accurate already-running/deferred response; no overlapping script/log edits | PROPOSED / NOT TESTED |
| Scheduled `UpdateCheck` racing with manual **Check now** | No duplicate GitHub/apply/notify side effects; manual check remains read-only | PROPOSED / NOT TESTED |
| Scheduled stable update racing with explicit `ApplyUpdate` | One verified target and durable update attempt; no duplicate restart | PROPOSED / NOT TESTED |
| Update script launched, service restarts, another request arrives | Cross-process ownership either persists safely or resets only after verified terminal state | PROPOSED / NOT TESTED |
| Failure writing update script or log; failed `Popen` | No false started status; no orphaned busy flag or accidental retry | PROPOSED / NOT TESTED |
| Failed fetch/ff-merge/pip/service restart/health | No destructive operator-state rollback, preserve evidence, clear and testable recovery | PROPOSED / NOT TESTED |
| GitHub 403/429/network error with prior successful cached status | Distinguish last **successful** comparison from new **failed** check; never falsely show current | PROPOSED / NOT TESTED |
| Branch/revision from PR merge ref vs contributor head | Expose exactly the built SHA/ref; never infer head from merge-ref metadata | PROPOSED / NOT TESTED |

**Further source-observed status caveat:** `check_update()` persists the latest-tag/update Boolean without an explicit last-check success/error result, and it may notify/apply after a network request has completed. The PR 2 data model should define an ordering/single-flight rule for both refreshes and side effects so an older request cannot overwrite a newer result. Do not equate a local mutex with proof that no stale network result can arrive later.

### D. Acceptance and evidence amendments

- [ ] **PR 1:** Before submitting/promotion, actually run the committed regression suite at its exact head, boot both standard and browser image variants, inspect generated `_build_info.py`, verify OCI revisions and the actual authenticated Status/Update JSON; include release tag, branch build, PR merge ref and legacy-image cases. No earlier synthesized or isolated check substitutes for those execution results.
- [ ] **PR 2:** Make manual **Check now** non-mutating; ensure latest successful check, last attempt failure, unknown version and stale cache are distinct and concurrency-safe. Stable release comparison and nightly commit discovery have separate testable source identities.
- [ ] **PR 3:** Single-flight updater coordination and deterministic two-request/failure interleaving tests are mandatory alongside existing branch/worktree, ff-only, rollback, restart and health gates. This remains a separate source/Git install change, not Docker auto-apply.
- [ ] **PR 4:** Reuse shared component styling and the Sidebar v26 test *method* (not older snapshots/tests) for keyboard, theme, responsive layout, escaping, plugin/log conditional sections and three-tile layout. Cross-reference the independent general UI backlog PR #4, without replacing its ownership.
- [ ] **Review gates:** Before any code promotion, recheck source HEAD/ancestry, run focused + applicable integration tests and image checks, create the implementation PR by owner manual non-draft step, inspect CodeRabbit actual comments/threads after completion, and independently verify final SHA. Human browser preview, deployed image digest and Docker host-side updater are separate gates.
- [ ] **No application/production/host authorization:** This supplement authorizes/records **documentation updates only**; fork default branch, implementation branch code, upstream publication and private Docker production/preview remain unchanged unless separately approved.

### E. Dated verification status at this supplement

| Scope | Result |
|---|---|
| Fork/upstream default refs | Read-only **IDENTICAL (0/0)** at `a41b8bd` during this audit |
| Backlog planning PR #6 and UI backlog #4 | Draft/open; planned dated Markdown + PR-body synchronization and independent readback |
| Existing isolated PR 1 candidate | `631933c`; six-file source diff and test definitions inspected; **NOT** submitted as a non-draft fork PR |
| Update concurrency and last-check semantics | Static flow/interleaving reviewed; runtime reproduction **NOT TESTED** |
| Full pytest, both Docker builds, CodeRabbit, live app, mobile UI, restart/recovery | **NOT TESTED** in this audit |
| Project Knowledge/OneDrive/public upstream | **NOT MODIFIED**; protected publication requires separate approval |
| GitHub Write/Preview of rendered GFM | **NOT VERIFIED** via API |

**Next safe continuation:** re-read the newest PR #6 body and Markdown first; then the cross-linked PR #4 and exact implementation branch `631933c`; audit/test the first PR with real image and API execution before assuming the UI has the data it needs. Keep this parent draft unmerged and preserve all original dated evidence above.


---

## 2026-11-10 maintainer-sized implementation scope — seven sequential PRs (LATEST PLAN)

> **Owner-requested scope-sizing amendment.** This section supersedes the earlier **five-PR** proposal and the later conversational **four-PR** compression *for future implementation planning*. Their earlier text remains intact as dated history. **Proxmox LXC installer and Windows desktop version-parity fixes are excluded from this project** and remain separately documented, optional findings, not requirements for shipping the Update page. No code, Docker host updater, production container, or protected Homelab reference changes are authorized by this planning amendment.

### Sizing evidence and principles

- Current official and fork `main` were independently confirmed identical at `a41b8bd` on 2026-11-10. [First implementation branch](https://github.com/TenchiMisaki/romarr/tree/feature/romarr-build-provenance-pr1) remains `631933c`; GitHub comparison with fork main reports **6 files, +212/-2 lines**, one commit. No implementation PR or exact-head CodeRabbit review for that branch was independently found. Both backlogs stay draft/open.
- PRs **2–7 file/line ranges below are planning estimates only**, **not** actual diffs or an hours estimate. All changing lines include test additions. Refine against each exact final implementation diff, prioritize one behavior per PR, and explicitly justify any larger scope. Do not split shared metadata producer/consumer changes merely to hit an arbitrary file or line count.
- Submit **one upstream implementation PR for maintainer review at a time**. Complete exact-head focused/full applicable testing and fork CodeRabbit review before upstream submission; wait for explicit maintainer disposition/merge or coordination before submitting the next dependent upstream PR. Multiple source branches may exist internally, but avoid overwhelming the maintainer with parallel requests.
- The existing [planning draft PR #6](https://github.com/TenchiMisaki/romarr/pull/6) is the one parent backlog; no seven new issue/backlog PRs need to be created in advance. Implementation PRs are new code PRs on isolated branches, not drafts/revisions of this notes branch, and are never silently pushed to upstream.

| Planned PR | One reviewable behavior | Expected changed paths / size | Dependency and independent acceptance gate | Priority |
|---|---|---|---|---|
| **1 — Build provenance** | Generate/validate release vs development image identity; expose exact built ref/revision in existing Status and Update APIs without enabling any updater | **Actual current branch: 6 files, +212/−2** | Current `631933c` needs real standard + browser Docker smoke build, actual metadata/API validation, focused/full applicable tests, exact-head CodeRabbit and owner promotion approval | First; existing candidate |
| **2 — Check-only and trustworthy status** | Separate **Check now** from auto-apply; expose checked/current/available/unknown/error and last-success vs last-attempt state without misleading stale flags | **Estimate 2–4 files, ~100–220 changed lines** | After PR 1 API shape; tests for unknown version, error/rate-limit, stale response, manual no-restart, compatibility and notification behavior | Second |
| **3 — Development/nightly commit checks** | Detect moving source revision independently of the stable latest-release endpoint; keep configured update channel distinct from build provenance | **Estimate 2–4 files, ~100–220 changed lines** | After PRs 1–2; tests for PR merge SHA vs HEAD identity, unchanged/ref-advanced, stable-vs-nightly, unknown build, safe update eligibility | Third |
| **4 — Existing Update UI + Docker guidance** | Keep exactly current three tiles, table, buttons, optional plugin/log sections; show compact build/ref and truthful status, effective Docker capability and non-destructive deployment-specific guidance | **Estimate 2–4 files, ~100–200 changed lines** | After PRs 1–3; browser/DOM, accessible keyboard, narrow viewport, escaping, theme and Docker unsupported/unknown state tests. No Docker self-update button | Fourth; visible outcome |
| **5 — Git updater single-flight** | At-most-one detached Git updater launch across concurrent scheduled/manual requests; avoid shared script/log overwrite and describe already-running state | **Estimate 2–3 files, ~140–280 changed lines** | After PR 2 manual/scheduler separation; deterministic two-request interleavings, launch failure, restart-crossing ownership and no-duplicate-side-effect tests. Source-derived risk, not a reproduced incident | Fifth; safety |
| **6 — Git targeting and clean preflight** | Verify Git checkout/branch, clean worktree, ref, ancestry, permissions and prerequisites; remove silent branch fallbacks and preserve unrelated files | **Estimate 2–3 files, ~100–220 changed lines** | After PR 5 single-flight as appropriate; fail-closed dirty/unknown/detached/mismatched branch, broken ref, unavailable dependency, no destructive side-effect tests | Sixth; safety |
| **7 — Git lifecycle and recovery** | Make detached update outcomes, dependency rollback, service restart/health and recovery reporting correct, observable and safe | **Estimate 2–3 files, ~150–300 changed lines** | After PRs 5–6; failure injection for fetch, merge, pip, restart, health and rollback, verified completion/error states, protected original and recovery. No live production fault injection | Seventh; safety |

### Submission and dependency strategy

1. **Publish only PR 1 first** after actual committed-head tests, both Docker image builds, API verification, fork review and owner approval. Existing branch is a candidate, not a passed image or accepted upstream contribution.
2. PRs **2 → 3** establish the back-end result contract separately from visual markup. The stable-release checker must continue failing closed for unknown build versions; nightly source-revision logic must not conflate a developer revision with an official release tag.
3. PR **4** implements the minimal approved existing-layout design **after** its data source stabilizes. Group UI and Docker guidance because they affect the same card/status story, but split them if the actual diff proves they require independent review, tests or behavior.
4. PRs **5 → 6 → 7** harden **Git/source install updates only**. These are separated because concurrency ownership, preflight targeting and lifecycle recovery have distinct fault-injection test contracts. Do not advertise automatic Git updates as newly certified until all three are accepted.
5. All future child branches must refresh against the *then current* approved upstream/fork base, not blindly rebase historical work. For each PR: inspect whole final diff, run tests on exact SHA, check CodeRabbit completed review comments/threads and CI, get owner approval, submit upstream, independently verify maintainer disposition; then update this backlog's dated progress record.
6. **Out of scope:** Proxmox installer scripts, Windows packaging, Docker host-side image auto-updater, production/preview CT107 mutations, global sidebar redesign or plugin update behavior. The external Docker host update investigation is optional and separately authorized after read-only deployment identification.
7. **Split control:** No fixed changed-line cutoff is a safety guarantee. If a planned PR exceeds its estimated scope or acquires a second unrelated behavior, pause *that PR only* for a scope review. Prefer a focused additional PR over submitting multiple independent faults/recovery systems in one diff. Conversely, a tiny fully coupled fix/test may remain one PR rather than manufacturing a dependency chain.

### Dated validation boundaries

- **PASS:** Read-only fork/upstream main identity and actual six-file PR 1 feature-branch diff at capture time.
- **SOURCE REVIEWED:** Existing Update page/handler, stable GitHub release query, scheduler, Git selfupdate and Docker help, plus the earlier Metadata/Sidebar audit lessons. This informs decomposition but does not prove future implementations.
- **NOT TESTED:** PRs 2–7 (no implementation), PR 1's real Docker image builds/authenticated API/full CI, CodeRabbit on this candidate, service restart/recovery, live/mobile UI, and current actual Docker deployment.
- **DOCUMENTATION UPDATE ONLY:** The updated PR #6 body and companion Markdown must be byte-identical after GitHub publication; keep this PR draft/open/labeled `backlog`. Any cross-branch/private Project Knowledge edit requires its own scope and verification.


### 2026-11-10 PR 1 focused validation and follow-up commit (latest implementation evidence)

The owner authorized continuing the agreed work via GitHub while away from the Proxmox system. **No Proxmox, Docker runtime, or main-branch action occurred.** The already isolated fork implementation branch `feature/romarr-build-provenance-pr1` advanced from `631933ccb57fa257b3b92bbdc0ec66be46a77a00` to [`fa2253fc31f1bfe400bb5d00dfe2ab87073d2147`](https://github.com/TenchiMisaki/romarr/commit/fa2253fc31f1bfe400bb5d00dfe2ab87073d2147) by one **scoped correction commit**. Changed paths in that commit: `romarr/build_info.py` and `tests/test_build_info.py`. It rejects empty/malformed branch/PR refs rather than incorrectly marking them verified Development builds; the final branch still changes only the original six PR 1 files relative to fork `main`. This corrects the earlier branch-head status, not historical review evidence.

**Reproduced test failure before correction:** Two additional local edge-case assertions expected unknown identity for `refs/heads/` and `refs/pull/`; both **FAILED** against the exact earlier source, which returned Development. The code fix and two committed regression functions now reject those refs.

**Focused tests actually performed, exact source identity:** Read the final branch files back from GitHub. Local isolated package copies of `romarr/build_info.py` (blob `606297a4f44694d7ac01e2c2155f9b27afcc6a8d`), `tests/test_build_info.py` (blob `0ccb35fabd3ca3cf4e475f7ff8b612f417261884`) and unchanged real `romarr/version.py` (blob `a3bd47afbc3047b0408dcf289e04b9bfe9372c43`) were independently matched to GitHub blob SHA using `git hash-object`. With a minimal local package `__init__.py`, pytest executed **16 functional cases: 16 PASS, 0 FAIL**, comprising ten committed functional tests and six local additional probes. The two committed repository-structure/static tests were **deselected** because a complete checked-out repository was unavailable in the isolated test environment. Python compilation passed. The literal Dockerfile metadata generator Python snippet parsed and executed with only its output path redirected to a disposable directory, and generated metadata was successfully imported/read by `get_build_info()`. This is **not an actual Docker image build or boot**.

**Still unverified:** full repository pytest (including the two deselected checks), both actual Docker image builds/boot/smoke gates, CI, authenticated update/status API runtime behavior, GitHub PR and CodeRabbit exact-head review, and production/preview Docker deployment. No non-draft PR was discovered for the feature branch at final readback. The owner remains responsible for manual fork code-PR creation per `70` §1.5.

**Next safe step:** prepare the maintainer-facing non-draft fork PR description and verify its exact GitHub compare link for branch `fa2253f`; allow the owner to submit it manually. After creation, independently inspect CodeRabbit review and CI at the exact submitted SHA. Do not promote to upstream or deploy absent their separate approval gates.


### 2026-11-10 fork PR #7 CodeRabbit follow-up — focused correction

- **Implementation PR created in owner fork:** [TenchiMisaki/romarr#7](https://github.com/TenchiMisaki/romarr/pull/7), non-draft, open, base `main`, head `feature/romarr-build-provenance-pr1`. The owner explicitly authorized the assistant to open **fork-local** code PRs while away from Proxmox. This observed successful creation supersedes the **manual-only fork PR creation requirement** for this owner-authorized instance; the protected `70` reference itself remains unchanged pending separately approved governance edit. **No upstream PR, merge or deployment** was performed.
- First CodeRabbit review completed on `fa2253fc31f1bfe400bb5d00dfe2ab87073d2147` (bot check `success` means complete). It reported **one trivial test-strengthening nitpick**: both Docker smoke checks accepted either `release` or `development` rather than the expected type derived from `github.ref`. It also recorded a **docstring coverage warning** (33.33% vs required 80%). Zero inline review threads were found. Neither finding was a proven runtime incident; the bot reported low merge risk.
- **Correction pushed to the same PR branch:** [`bea96dcbdcbbb92530f53aeb8c1e334c51b178c7`](https://github.com/TenchiMisaki/romarr/commit/bea96dcbdcbbb92530f53aeb8c1e334c51b178c7), parent `fa2253f`, exact three-file follow-up: `.github/workflows/docker.yml`, `romarr/build_info.py`, `tests/test_build_info.py`. Both smoke calls now check `b["type"] == os.environ["EXPECTED_BUILD_TYPE"]` with GitHub-ref-derived expected type, preserving existing revision/ref assertions. Only meaningful docstrings were added to the provenance helper and tests, plus a focused regression asserting that **both** smoke commands enforce the expected kind. Runtime provenance classification and both Status/Update APIs remain unchanged.
- **Verification:** The final helper/test blobs `106da8a882b270798e84faf45e1e2a4139c416a2` and `a79baaac35ae08f592bd493dcb89c719791391e3` matched the hash of locally edited test sources, and workflow blob `2a1662fa910d45f5f03a3b8a599f3cdbd1c8ef9f` was independently read back from the pushed branch. Isolated pytest using actual `romarr/version.py`: **16 passed, 0 failed, three repository-structure tests deselected** (no complete local checkout). Python compilation passed. Four synthetic runtime smoke-code cases passed for expected/wrong Release and Development metadata. Local AST inspection confirms both touched production helper functions and all 14 test-module functions contain docstrings; **this is not proof CodeRabbit's threshold passed**.
- **New review status at time of branch readback:** CodeRabbit automatically began a new review on exact commit `bea96dc`, **IN PROGRESS** at this observation. Prior review is now superseded. GitHub Actions full tests, actual standard/browser image builds, authenticated API integration, live CT107 deployment and CodeRabbit's **second** quality outcome remained **NOT VERIFIED**. No `main` branch changed. Continue by checking the new exact-head check, complete review text, all threads and CI; do not claim final acceptance until independently confirmed.
