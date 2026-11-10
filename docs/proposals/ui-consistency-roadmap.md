**Documentation-only backlog / technical continuation record. DRAFT — DO NOT MERGE.**

Preserve the planned ROMarr UI consistency initiative so a future session can resume without relying on conversation memory. Header/sidebar alignment comes first, followed by a comprehensive page audit and small, independently verified cleanup changes. This record does not implement or deploy the initiative.

## 1. Authorization, scope and provenance

Prepared November 9, 2026 (America/Los_Angeles). The owner explicitly authorized one documentation-only draft Backlog PR in the personal fork, a new isolated notes branch from fork main, a companion file under docs/proposals/, and the complete same record in the PR body. No application changes, production/preview operations, upstream submission, main-branch update or merge are authorized by this task.

The initiating discussion was “UI Polish: Standardize Header Height.” The owner described cleaning up all the various pages as a major goal and identified header alignment as the first step. The later “Bug: Zip instead a Zip Issue” discussion established Backlog PRs as complete future-session handoffs, not short feature summaries. Its November 9 closeout reports that updated Homelab references 00 and 70 were published, including decision HL-GIT-03 and section 1.1. The owner directed this session to that discussion after older local references were found.

**Reference access limitation:** Local copies of 00/10/50/70 were consulted for relevant history, boundaries and process. Local 00/70 predate the November 9 backlog amendment. The November 9 publication confirmation and process were recovered from the named conversation; the updated Project Knowledge files themselves were not independently read or hash-verified in this session. Do not label this a fresh full current-document audit. The owner's current explicit instructions specify the backlog procedure used here.

Private source records remain private. Do not publish local hostnames, IP addresses, account paths, credentials, configuration, browser sessions, ROM files or download details in future additions.

## 2. Pinned repository state and related work

- Personal fork: [TenchiMisaki/romarr](https://github.com/TenchiMisaki/romarr), public, main verified at `041a367cedeb1c4b66365a9daea6a095cc753d55`.
- Upstream: [BlizzHacker/romarr](https://github.com/BlizzHacker/romarr), main verified at `9bf31ffcef3913798252e4c678f12f1544b07a2a`.
- Notes branch: `notes/ui-consistency-roadmap`, created from the pinned personal-fork main, not the newer upstream main or an existing contribution/review branch.
- Companion record: `docs/proposals/ui-consistency-roadmap.md`.
- Fork PR inventory checked across all states: #1 metadata correction review (merged), [#2 full metadata comparison](https://github.com/TenchiMisaki/romarr/pull/2) (open review-only), and [#3 BlueRoms backlog](https://github.com/TenchiMisaki/romarr/pull/3) (open). No duplicate UI consistency backlog found.
- Upstream PR inventory checked across all states. [#134](https://github.com/BlizzHacker/romarr/pull/134) and [#136](https://github.com/BlizzHacker/romarr/pull/136) already merged responsive sidebar work. Preserve and evaluate that implementation rather than proposing it as missing.
- [#140 Metadata persistence](https://github.com/BlizzHacker/romarr/pull/140) is now merged, as is [#143](https://github.com/BlizzHacker/romarr/pull/143). Earlier discussion calling #140 active is historical. Do not modify its branches or mix its behavior into this initiative.
- GitHub Issues remain disabled on the fork. Earlier attempts to use parent/child issues failed according to the prior discussion; no issue numbers were actually created. Previously suggested roadmap issue numbers were illustrative. Do not repeat the incorrect Settings-link detour or change repository settings to implement this backlog.

These are point-in-time repository facts, not proof of released, installed or browser-verified behavior. Fork main differs from upstream main; no synchronization is part of this record.

## 3. Intended outcome and constraints

Make existing ROMarr pages visually consistent while preserving the current design, navigation and behavior. Avoid a broad redesign, feature removal or one large cleanup patch. Shared layout corrections should precede repeated page-specific overrides.

Initial goal: align the sidebar brand/header and page top bar so their boundaries are visually coherent at applicable desktop sizes, with intentional responsive behavior. Exact pixel height, accepted tolerance and whether wrapping requires a minimum rather than fixed height are **UNDECIDED**. No current screenshot measurements or reproduced defect are claimed.

Preserve navigation groups, selected-route indication, search, theme/accent controls, keyboard operation, mobile drawer, focus handling, scrolling, existing accessible names and no-script fallback. Do not make Metadata lookups, settings persistence or other asynchronous interactions regress as an incidental layout change.

## 4. Source inspection and implementation anchors

Focused source inspection only, against [romarr/ui.py at the pinned upstream revision](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py). This is not a full source review, browser reproduction or validated patch.

Relevant locations at that revision:

- Around lines 118–191: sidebar rail, brand area, footer and sticky top-bar styles; inspect actual padding, borders, font metrics, controls and box sizing together.
- Around lines 481–507: earlier 820px and 540px responsive rules change rail widths, brand sizing/padding and top padding.
- Around lines 511–560: later category-navigation rules redefine rail width and provide the 700px drawer transition; the 701–820px rule adjusts main margin. CSS cascade/order is relevant. Do not edit an earlier rule in isolation and assume it wins.
- Around lines 578–605: no-script navigation/theme fallback rules.
- Around lines 1103–1172: sidebar interaction/focus-related code to inspect before changing structural markup.
- Around line 1228: route-specific top title assignment; around line 1238: page-renderer registry begins.
- Around line 5758 onward: navigation markup and native toggle.

The presence of multiple media rules is a source observation, not proof of the visual defect's root cause. Future investigation must inspect the complete relevant selectors, markup, renderer lifecycle and tests at a freshly pinned revision.

**Proposed approach, not implemented:** measure existing top/brand bounding boxes and computed styles, then consider one shared header sizing rule or token with consistent border/box sizing and alignment. Prefer minimum sizing that accommodates content where appropriate; do not force a chosen height before testing long titles, zoom and mobile controls. Preserve intentional differences between permanent desktop navigation and the mobile drawer.

## 5. Incremental roadmap

- [ ] Establish an isolated baseline and reproduce/measure header alignment.
- [ ] Implement and validate the smallest header/sidebar alignment correction under separate development authorization.
- [ ] Audit every actual route/page from the then-current navigation and renderer inventory.
- [ ] Define concise shared standards for header geometry, spacing, margins, section headings, reusable layout and control placement.
- [ ] Standardize filters, search fields, dropdowns and buttons without changing their functional semantics.
- [ ] Address confirmed page-specific inconsistencies in small independent changes.
- [ ] Validate responsive behavior across pages and retain before/after evidence.

Do not freeze a historical count of 31 or 32 pages into the acceptance criterion. Generate the current route inventory, including conditional/hidden pages, and record exclusions with reasons.

For each audited page capture route/name, source renderer, viewport and theme, observed layout, intended exception versus actual inconsistency, reproducible steps, screenshot/measurement evidence where useful, impact, proposed smallest correction and acceptance checks.

Prioritize overlapping/clipped/unusable content above inconsistent layout or filter placement, and those above minor whitespace or subtle alignment polish. These are triage rules, not claims that every listed defect exists.

## 6. Validation and acceptance plan

All future behavior checks below are **NOT TESTED for this initiative**.

| Area | Required evidence |
|---|---|
| Header alignment | Before/after geometry at the same viewport, font state and zoom; documented intended boundary and tolerance |
| Breakpoints | Wide desktop and immediately around current 820px, 700px and 540px rules; inspect actual current breakpoints again |
| Content stress | Long page titles, search field, visible controls, text zoom and narrow windows without clipping or overlap |
| Navigation | Every route remains reachable; group expansion and selected state preserved; Back/Forward and direct navigation work |
| Mobile drawer | Open/close, scrim, focus entry/return, keyboard behavior, scrolling and viewport-height handling preserved |
| Accessibility | Visible focus, readable contrast, zoom/reflow, reduced motion and meaningful control names |
| Themes | Existing light/dark/sepia and accent choices remain legible and aligned |
| Fallback | Existing no-script behavior remains usable where supported |
| Functional regression | Relevant page controls, forms and asynchronous navigation remain operational |
| Review | Inspect entire scoped diff, run relevant existing tests and CodeRabbit, disposition findings; report missing coverage |
| Runtime | Separately authorized isolated preview verification, exact restore and stable health evidence if preview is modified |

Tests must match the change. Static syntax, simulated DOM, screenshots, CodeRabbit and actual application tests are distinct evidence. No previous Metadata test count or upstream suite report proves this UI initiative works.

## 7. Safety, recovery and rejected shortcuts

Keep production, shared downloads, real ROM libraries and protected Project Knowledge unchanged. A preview container is not assumed safe merely because it has a separate name: prior documentation records shared writable download access. Future UI tests should avoid acquisition/import/cleanup and use isolated benign fixtures where needed.

If later authorized to patch preview, first verify node and guest identity, service/container/image/source, access, backup and recovery prerequisites. Preserve the exact original outside the container, provide independent recovery and immediate revert, restart only the approved service if necessary, restore the exact original by hash and verify stability. Recheck current 10/50 safeguards, including any newer recovery requirements, before APPLY. A restart alone does not remove a source patch.

Rejected or deferred approaches: broad redesign; unmeasured arbitrary fixed heights; page-by-page duplicated CSS when a shared correction is appropriate; issue creation requiring a settings detour; mixing with Metadata review work; assuming merged means installed; promoting source inspection into runtime PASS.

No runtime change occurs for this backlog, so operational rollback is not required. This notes branch and draft are the durable record; do not merge or delete them automatically.

## 8. Evidence gaps and continuation checklist

Missing: original detailed header screenshots/measurements, any earlier exact CSS proposal not present in the retrieved discussion, a full current page inventory, complete source-review coverage, local installed revision, browser/device baseline and automated regression fixtures for this initiative. Do not reconstruct missing evidence from guesses.

On resumption:

1. Read this entire PR body and companion file; compare for drift and preserve newer evidence.
2. Read actual newest Homelab 00/10/50/70, especially 70 section 1.1; do not treat the older local copies as current.
3. Recheck fork/upstream main, related issues/PRs, existing backlog and relevant releases. Determine whether upstream already addressed the intended behavior.
4. Pin an implementation baseline separately from this historical notes-branch base; preserve all existing main/contribution/review branches.
5. Recover prior screenshots or reproduce the alignment with recorded viewport, theme, zoom and source revision.
6. Complete relevant source and page inventory, choose the smallest correction, and obtain the appropriate development/runtime authorization before implementation.
7. Run meaningful tests, review and isolated visual acceptance; preserve failures and coverage gaps.
8. Update both this file and the full PR body with findings, rejected attempts, exact source/test evidence and next steps under the applicable authorization.
9. Consider a separate upstream submission only after its independent source-review, verification, Preview and owner-approval requirements are met.

## 9. Verification evidence for this documentation task

Performed: prior-conversation recovery; relevant local reference consultation with version limitation disclosed; live fork/upstream identities and SHAs; all-state PR and fork branch inventories; focused pinned UI source inspection; raw Markdown/link structure review and privacy review. No duplicate UI backlog appeared in the inspected fork PR inventory.

Official guidance consulted: [creating a pull request](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request) and [GitHub Markdown syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

**GITHUB PREVIEW: NOT VERIFIED.** Native Write/Preview was not inspected. API readback is separate from rendered Preview and does not certify upstream submission readiness.

Application code changes: NONE. Production/preview operations: NONE. Runtime tests: NONE. Full codebase review: NOT PERFORMED. CodeRabbit review: NOT RUN for this documentation record. This draft records future work; it does not claim that the UI defect is fixed.
