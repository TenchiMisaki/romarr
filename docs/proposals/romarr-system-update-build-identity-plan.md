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
